"""Investigator command-centre endpoints (demo-token protected)."""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import INVESTIGATOR_DEMO_TOKEN
from ..database import get_db
from ..models import AuditLog, Case, ExtractedEntity, ReviewDecision, RiskEvent

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def require_investigator(x_investigator_token: str = Header(default="")):
    """Demo-only role gate. Clearly not production auth; documented as such."""
    if x_investigator_token != INVESTIGATOR_DEMO_TOKEN:
        raise HTTPException(401, "Investigator demo token required (see docs).")
    return "demo-investigator"


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: str = Depends(require_investigator)):
    total = db.query(Case).count()
    critical = db.query(Case).filter(Case.severity == "Critical").count()
    high = db.query(Case).filter(Case.severity == "High").count()
    open_cases = db.query(Case).filter(Case.status == "open").count()
    reviewed = db.query(Case).filter(Case.status == "reviewed").count()
    hindi = db.query(Case).filter(Case.language == "hi").count()
    prevented = db.query(Case).filter(Case.payment_prevented.is_(True)).count()

    def repeated(entity_type: str):
        rows = (
            db.query(ExtractedEntity.masked, func.count(func.distinct(ExtractedEntity.case_id)))
            .filter(ExtractedEntity.entity_type == entity_type)
            .group_by(ExtractedEntity.normalized, ExtractedEntity.masked)
            .having(func.count(func.distinct(ExtractedEntity.case_id)) >= 2)
            .order_by(func.count(func.distinct(ExtractedEntity.case_id)).desc())
            .limit(8)
            .all()
        )
        return [{"masked": m, "cases": c} for m, c in rows]

    # Average first-detection point: earliest message seq where cumulative risk crossed 50.
    detection_seqs = []
    payment_detections = 0
    payment_cases = 0
    for case in db.query(Case).filter(Case.final_risk_score >= 50).all():
        crossed = next((m for m in case.messages if m.cumulative_risk >= 50), None)
        if crossed:
            detection_seqs.append(crossed.seq + 1)
        payment_seq = next(
            (
                m.seq
                for m in case.messages
                if any(s.get("stage") == "payment_or_access_request" for s in (m.detected_signals or []))
            ),
            None,
        )
        if payment_seq is not None:
            payment_cases += 1
            if crossed and crossed.seq <= payment_seq:
                payment_detections += 1

    return {
        "total_complaints": total,
        "critical_cases": critical,
        "high_cases": high,
        "open_cases": open_cases,
        "reviewed_cases": reviewed,
        "hindi_cases": hindi,
        "english_cases": total - hindi,
        "payments_prevented": prevented,
        "repeated_phones": repeated("phone"),
        "repeated_upi_ids": repeated("upi_id"),
        "avg_detection_message": round(sum(detection_seqs) / len(detection_seqs), 1) if detection_seqs else None,
        "detected_before_payment_pct": round(payment_detections / payment_cases * 100, 1) if payment_cases else None,
    }


@router.get("/emerging-patterns")
def emerging_patterns(db: Session = Depends(get_db), _: str = Depends(require_investigator)):
    rows = (
        db.query(RiskEvent.stage, RiskEvent.label, func.count(RiskEvent.id))
        .filter(RiskEvent.kind == "signal")
        .group_by(RiskEvent.stage, RiskEvent.label)
        .order_by(func.count(RiskEvent.id).desc())
        .limit(12)
        .all()
    )
    categories = (
        db.query(Case.suspected_category, func.count(Case.id))
        .group_by(Case.suspected_category)
        .order_by(func.count(Case.id).desc())
        .all()
    )
    return {
        "top_signals": [{"stage": s, "label": l, "count": c} for s, l, c in rows],
        "categories": [{"category": cat, "count": c} for cat, c in categories],
    }


@router.get("/hotspots")
def hotspots(db: Session = Depends(get_db), _: str = Depends(require_investigator)):
    """Synthetic geographic distribution — city labels come from seed/demo data."""
    rows = (
        db.query(Case.city, func.count(Case.id), func.avg(Case.final_risk_score))
        .filter(Case.city != "")
        .group_by(Case.city)
        .all()
    )
    return {
        "synthetic": True,
        "cities": [
            {"city": city, "cases": count, "avg_risk": round(avg or 0, 1)}
            for city, count, avg in rows
        ],
    }


@router.get("/watchlist")
def watchlist(db: Session = Depends(get_db), _: str = Depends(require_investigator)):
    rows = (
        db.query(
            ExtractedEntity.entity_type,
            ExtractedEntity.masked,
            func.count(func.distinct(ExtractedEntity.case_id)).label("cases"),
        )
        .filter(ExtractedEntity.entity_type.in_(["phone", "upi_id", "bank_account", "url"]))
        .group_by(ExtractedEntity.entity_type, ExtractedEntity.normalized, ExtractedEntity.masked)
        .order_by(func.count(func.distinct(ExtractedEntity.case_id)).desc())
        .limit(20)
        .all()
    )
    return [
        {"entity_type": t, "masked": m, "cases": c, "watch": c >= 2}
        for t, m, c in rows
    ]


@router.get("/reviews")
def reviews(db: Session = Depends(get_db), _: str = Depends(require_investigator)):
    rows = db.query(ReviewDecision).order_by(ReviewDecision.created_at.desc()).limit(50).all()
    return [
        {
            "case_id": r.case_id,
            "reviewer": r.reviewer,
            "decision": r.decision,
            "notes": r.notes,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
