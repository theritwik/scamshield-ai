"""Fraud graph service backed by the relational store, analysed with NetworkX."""
import networkx as nx
from sqlalchemy.orm import Session

from ..models import Case, ExtractedEntity, FraudGraphEdge, FraudGraphNode

ENTITY_NODE_TYPES = {
    "phone", "upi_id", "bank_account", "email", "url", "ifsc",
    "officer_name", "remote_tool",
}

RELATIONS = {
    "phone": "called_from",
    "upi_id": "requested_payment_to",
    "bank_account": "requested_payment_to",
    "email": "mentioned_in",
    "url": "mentioned_in",
    "ifsc": "mentioned_in",
    "officer_name": "claimed_officer",
    "remote_tool": "requested_install",
}


def node_id(node_type: str, normalized: str) -> str:
    return f"{node_type}:{normalized}"[:64]


def sync_case(db: Session, case: Case, entities: list[ExtractedEntity]) -> None:
    """Upsert the case node and its entity nodes/edges after an analysis."""
    cid = node_id("complaint", case.id)
    complaint = db.get(FraudGraphNode, cid)
    if not complaint:
        complaint = FraudGraphNode(
            id=cid, node_type="complaint", label=case.case_number,
            masked_label=case.case_number, risk=0.0,
        )
        db.add(complaint)
    complaint.risk = case.final_risk_score
    complaint.meta = {
        "case_id": case.id, "severity": case.severity,
        "category": case.suspected_category, "city": case.city,
    }

    existing_edges = {
        (e.source, e.target)
        for e in db.query(FraudGraphEdge).filter(FraudGraphEdge.case_id == case.id)
    }
    for ent in entities:
        if ent.entity_type not in ENTITY_NODE_TYPES:
            continue
        nid = node_id(ent.entity_type, ent.normalized)
        node = db.get(FraudGraphNode, nid)
        if not node:
            node = FraudGraphNode(
                id=nid, node_type=ent.entity_type,
                label=ent.normalized, masked_label=ent.masked, risk=0.0,
            )
            db.add(node)
        node.risk = max(node.risk, case.final_risk_score)
        if (cid, nid) not in existing_edges:
            db.add(
                FraudGraphEdge(
                    source=cid, target=nid,
                    relation=RELATIONS.get(ent.entity_type, "mentioned_in"),
                    case_id=case.id,
                )
            )
            existing_edges.add((cid, nid))


def build_graph(db: Session) -> nx.Graph:
    g = nx.Graph()
    for n in db.query(FraudGraphNode).all():
        g.add_node(
            n.id, node_type=n.node_type, label=n.label,
            masked_label=n.masked_label, risk=n.risk, meta=n.meta or {},
        )
    for e in db.query(FraudGraphEdge).all():
        if g.has_node(e.source) and g.has_node(e.target):
            g.add_edge(e.source, e.target, relation=e.relation, case_id=e.case_id)
    return g


def network_payload(db: Session, reveal: bool = False, focus_case_id: str | None = None) -> dict:
    """Serialise the graph with analysis annotations for the frontend."""
    g = build_graph(db)
    if focus_case_id:
        cid = node_id("complaint", focus_case_id)
        if g.has_node(cid):
            keep = {cid} | set(g.neighbors(cid))
            for n in list(g.neighbors(cid)):
                keep |= set(g.neighbors(n))
            g = g.subgraph(keep).copy()
        else:
            g = nx.Graph()

    degree = dict(g.degree())
    centrality = nx.degree_centrality(g) if g.number_of_nodes() > 1 else {}
    components = list(nx.connected_components(g))
    comp_index = {n: i for i, comp in enumerate(components) for n in comp}

    # Mule-account heuristic: payment endpoints reached from multiple complaints.
    mule_candidates = []
    for n, d in g.nodes(data=True):
        if d["node_type"] in ("upi_id", "bank_account"):
            complaint_links = sum(
                1 for nb in g.neighbors(n) if g.nodes[nb]["node_type"] == "complaint"
            )
            if complaint_links >= 2:
                mule_candidates.append(
                    {
                        "id": n,
                        "label": d["label"] if reveal else d["masked_label"],
                        "type": d["node_type"],
                        "complaints": complaint_links,
                        "risk": d["risk"],
                    }
                )
    mule_candidates.sort(key=lambda m: (-m["complaints"], -m["risk"]))

    nodes = [
        {
            "id": n,
            "type": d["node_type"],
            "label": d["label"] if reveal else d["masked_label"],
            "risk": d["risk"],
            "degree": degree.get(n, 0),
            "centrality": round(centrality.get(n, 0.0), 3),
            "component": comp_index.get(n, 0),
            "meta": d.get("meta", {}),
        }
        for n, d in g.nodes(data=True)
    ]
    edges = [
        {"source": u, "target": v, "relation": d.get("relation", "")}
        for u, v, d in g.edges(data=True)
    ]

    insights = []
    for m in mule_candidates[:5]:
        insights.append(
            f"{m['type'].replace('_', ' ').title()} {m['label']} appears in {m['complaints']} "
            f"separate complaints — a suspected mule endpoint that requires human verification."
        )
    big = max(components, key=len, default=set())
    if len(big) >= 5:
        complaints_in_big = sum(1 for n in big if g.nodes[n]["node_type"] == "complaint")
        if complaints_in_big >= 2:
            insights.append(
                f"A connected cluster links {complaints_in_big} complaints through "
                f"{len(big) - complaints_in_big} shared identifiers — potentially one operation."
            )

    return {
        "nodes": nodes,
        "edges": edges,
        "components": len(components),
        "suspected_mules": mule_candidates,
        "insights": insights,
        "disclaimer": "Links show reported associations in synthetic demo data, not criminal guilt.",
    }
