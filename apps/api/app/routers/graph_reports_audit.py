"""Fraud graph, evidence report and audit endpoints."""
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import ENGINE_VERSION, INVESTIGATOR_DEMO_TOKEN
from ..database import get_db
from ..models import AuditLog, Case, EvidenceReport
from ..services import audit, graph, report
from .dashboard import require_investigator

router = APIRouter(prefix="/api", tags=["graph", "reports", "audit"])


@router.get("/graph/network")
def graph_network(
    db: Session = Depends(get_db),
    x_investigator_token: str = Header(default=""),
):
    # Investigators (demo token) may reveal seeded synthetic identifiers.
    reveal = x_investigator_token == INVESTIGATOR_DEMO_TOKEN
    return graph.network_payload(db, reveal=reveal)


@router.get("/cases/{case_id}/graph")
def case_graph(
    case_id: str,
    db: Session = Depends(get_db),
    x_investigator_token: str = Header(default=""),
):
    if not db.get(Case, case_id):
        raise HTTPException(404, "Case not found")
    reveal = x_investigator_token == INVESTIGATOR_DEMO_TOKEN
    return graph.network_payload(db, reveal=reveal, focus_case_id=case_id)


@router.post("/cases/{case_id}/generate-report")
def generate_report(case_id: str, db: Session = Depends(get_db)):
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    if not case.messages:
        raise HTTPException(422, "Nothing to report: the case has no conversation yet.")
    path = report.generate_pdf(db, case)
    sha = report.sha256_file(path)
    row = EvidenceReport(
        case_id=case.id, file_path=str(path), sha256=sha, engine_version=ENGINE_VERSION
    )
    db.add(row)
    audit.record(db, "citizen", "report_generated", case.id, meta={"sha256": sha})
    db.commit()
    return {"report_id": row.id, "sha256": sha, "download": f"/api/reports/{row.id}"}


@router.get("/reports/{report_id}")
def download_report(report_id: str, db: Session = Depends(get_db)):
    row = db.get(EvidenceReport, report_id)
    if not row:
        raise HTTPException(404, "Report not found")
    return FileResponse(
        row.file_path,
        media_type="application/pdf",
        filename=row.file_path.split("/")[-1],
    )


@router.get("/audit/{case_id}")
def case_audit(case_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case_id)
        .order_by(AuditLog.timestamp)
        .all()
    )
    return [
        {
            "event_id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "actor": a.actor,
            "action": a.action,
            "case_id": a.case_id,
            "meta": a.meta,
            "previous_value": a.previous_value,
            "new_value": a.new_value,
        }
        for a in rows
    ]


@router.get("/audit")
def all_audit(db: Session = Depends(get_db), _: str = Depends(require_investigator)):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
    return [
        {
            "event_id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "actor": a.actor,
            "action": a.action,
            "case_id": a.case_id,
            "meta": a.meta,
        }
        for a in rows
    ]
