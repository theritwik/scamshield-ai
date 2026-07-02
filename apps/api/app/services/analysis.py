"""Orchestrates a full case analysis: engine run, entities, reputation, graph, audit."""
import time

from sqlalchemy.orm import Session

from ..config import ENGINE_VERSION
from ..engine.entities import extract_entities
from ..engine.risk_engine import (
    ConversationState,
    analyse_message,
    summarise,
)
from ..models import (
    Case,
    ExtractedEntity,
    ReportedEntity,
    RiskAssessment,
    RiskEvent,
)
from . import audit, graph


def reported_set(db: Session, entities) -> set[str]:
    if not entities:
        return set()
    norms = [e.normalized for e in entities]
    rows = (
        db.query(ReportedEntity.normalized)
        .filter(ReportedEntity.normalized.in_(norms))
        .all()
    )
    return {r[0] for r in rows}


def analyse_case(db: Session, case: Case, actor: str = "citizen") -> dict:
    """Re-run the sequence-aware engine over the whole conversation and persist results."""
    started = time.perf_counter()

    db.query(RiskEvent).filter(RiskEvent.case_id == case.id).delete()
    db.query(ExtractedEntity).filter(
        ExtractedEntity.case_id == case.id, ExtractedEntity.source == "message"
    ).delete()

    state = ConversationState()
    analyses = []
    all_entities: dict[tuple[str, str], ExtractedEntity] = {}

    # Include evidence-derived text (OCR/QR/transcripts) entities in reputation checks.
    extra_entities = (
        db.query(ExtractedEntity)
        .filter(ExtractedEntity.case_id == case.id, ExtractedEntity.source != "message")
        .all()
    )
    for e in extra_entities:
        all_entities[(e.entity_type, e.normalized)] = e

    for msg in case.messages:
        ents = extract_entities(msg.text)
        reported = set()
        known = reported_set(db, ents)
        for ent in ents:
            key = (ent.entity_type, ent.normalized)
            if key not in all_entities:
                row = ExtractedEntity(
                    case_id=case.id,
                    entity_type=ent.entity_type,
                    value=ent.value,
                    normalized=ent.normalized,
                    masked=ent.masked,
                    source="message",
                    first_seen_seq=msg.seq,
                    previously_reported=ent.normalized in known,
                )
                db.add(row)
                all_entities[key] = row
            if ent.normalized in known:
                reported.add(ent.normalized)

        analysis = analyse_message(state, msg.seq, msg.speaker, msg.text, reported)
        msg.detected_signals = [
            {
                "signal_id": h.signal_id,
                "stage": h.stage,
                "label": h.label,
                "label_hi": h.label_hi,
                "weight": h.weight,
                "excerpt": h.matched_text,
                "explanation": h.explanation,
                "explanation_hi": h.explanation_hi,
                "kind": h.kind,
            }
            for h in analysis.hits
        ]
        msg.risk_delta = analysis.risk_delta
        msg.cumulative_risk = analysis.cumulative_risk
        analyses.append(analysis)

        for h in analysis.hits:
            db.add(
                RiskEvent(
                    case_id=case.id,
                    message_id=msg.id,
                    seq=msg.seq,
                    stage=h.stage,
                    signal_id=h.signal_id,
                    label=h.label,
                    weight=h.weight,
                    kind=h.kind,
                    explanation=h.explanation,
                )
            )

    result = summarise(state, analyses)
    prev = f"{case.final_risk_score:.0f}/{case.severity}"
    case.final_risk_score = result["score"]
    case.severity = result["severity"]
    case.confidence = result["confidence"]
    case.suspected_category = result["category"]
    if result["severity"] in ("High", "Critical"):
        case.payment_prevented = True

    db.add(
        RiskAssessment(
            case_id=case.id,
            score=result["score"],
            severity=result["severity"],
            confidence=result["confidence"],
            category=result["category"],
            stages_detected=result["stages_detected"],
            top_reasons=result["top_reasons"],
            recommended_actions=result["recommended_actions"],
            missing_evidence=result["missing_evidence"],
            false_positive_caution=result["false_positive_caution"],
            engine_version=ENGINE_VERSION,
        )
    )

    graph.sync_case(db, case, list(all_entities.values()))
    audit.record(
        db, actor, "analysis_performed", case.id,
        meta={"messages": len(analyses), "engine": ENGINE_VERSION},
        previous_value=prev,
        new_value=f"{result['score']:.0f}/{result['severity']}",
    )

    result["engine_version"] = ENGINE_VERSION
    result["processing_ms"] = round((time.perf_counter() - started) * 1000, 1)
    result["timeline"] = [
        {
            "seq": a.seq,
            "speaker": a.speaker,
            "risk_delta": a.risk_delta,
            "cumulative_risk": a.cumulative_risk,
            "stages": a.stages,
        }
        for a in analyses
    ]
    return result
