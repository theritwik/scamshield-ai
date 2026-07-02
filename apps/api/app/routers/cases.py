"""Case, message, evidence and analysis endpoints."""
import hashlib
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import ALLOWED_UPLOAD_TYPES, ENGINE_VERSION, MAX_UPLOAD_BYTES, UPLOAD_DIR
from ..database import get_db
from ..engine.entities import extract_entities, mask
from ..models import (
    Case,
    ConversationMessage,
    EvidenceFile,
    ExtractedEntity,
    ReviewDecision,
    RiskAssessment,
)
from ..schemas import (
    CaseCreate,
    CaseDetailOut,
    CaseOut,
    ManualEntity,
    MessageCreate,
    MessagesBulkCreate,
    ReviewCreate,
)
from ..services import audit, media
from ..services.analysis import analyse_case, reported_set

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _case_number(db: Session) -> str:
    n = db.query(Case).count() + 1
    return f"SSA-{datetime.now(timezone.utc):%Y}-{n:05d}"


def _get_case(db: Session, case_id: str) -> Case:
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return case


@router.post("", response_model=CaseOut, status_code=201)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    if not payload.consent_given:
        raise HTTPException(422, "Consent is required to analyse a conversation.")
    case = Case(
        case_number=_case_number(db),
        title=payload.title,
        language=payload.language,
        source_type=payload.source_type,
        consent_given=True,
        city=payload.city,
    )
    db.add(case)
    db.flush()  # assign case.id before the audit record references it
    audit.record(db, "citizen", "case_created", case.id, meta={"language": case.language})
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db)):
    return db.query(Case).order_by(Case.created_at.desc()).limit(200).all()


@router.get("/{case_id}", response_model=CaseDetailOut)
def get_case(case_id: str, db: Session = Depends(get_db)):
    return _get_case(db, case_id)


@router.post("/{case_id}/messages")
def add_message(case_id: str, payload: MessageCreate, db: Session = Depends(get_db)):
    """Append one message and incrementally analyse — powers the live simulation."""
    case = _get_case(db, case_id)
    msg = ConversationMessage(
        case_id=case.id,
        seq=len(case.messages),
        speaker=payload.speaker,
        text=payload.text,
        language=payload.language,
    )
    db.add(msg)
    db.flush()
    db.refresh(case)  # pick up the new message in the loaded relationship
    result = analyse_case(db, case)
    db.commit()
    db.refresh(msg)
    return {
        "message": {
            "id": msg.id,
            "seq": msg.seq,
            "speaker": msg.speaker,
            "text": msg.text,
            "detected_signals": msg.detected_signals,
            "risk_delta": msg.risk_delta,
            "cumulative_risk": msg.cumulative_risk,
        },
        "assessment": result,
    }


@router.post("/{case_id}/messages/bulk")
def add_messages_bulk(case_id: str, payload: MessagesBulkCreate, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    base = len(case.messages)
    for i, m in enumerate(payload.messages):
        db.add(
            ConversationMessage(
                case_id=case.id, seq=base + i, speaker=m.speaker,
                text=m.text, language=m.language,
            )
        )
    db.flush()
    db.refresh(case)
    result = analyse_case(db, case)
    db.commit()
    return {"added": len(payload.messages), "assessment": result}


@router.post("/{case_id}/analyse")
def run_analysis(case_id: str, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    if not case.messages:
        raise HTTPException(422, "Add at least one message before analysing.")
    result = analyse_case(db, case)
    db.commit()
    return result


@router.post("/{case_id}/entities")
def add_manual_entity(case_id: str, payload: ManualEntity, db: Session = Depends(get_db)):
    """Register a phone/UPI/account the user was asked to pay — checks reputation."""
    case = _get_case(db, case_id)
    ents = extract_entities(payload.value)
    ents = [e for e in ents if e.entity_type == payload.entity_type] or None
    if ents is None:
        # Accept as-is with normalisation fallback so users can check any identifier.
        norm = re.sub(r"\s", "", payload.value.lower())
        from ..engine.entities import Entity

        ents = [Entity(payload.entity_type, payload.value, norm, mask(payload.entity_type, payload.value))]
    known = reported_set(db, ents)
    out = []
    for ent in ents:
        row = ExtractedEntity(
            case_id=case.id,
            entity_type=ent.entity_type,
            value=ent.value,
            normalized=ent.normalized,
            masked=ent.masked,
            source="manual",
            previously_reported=ent.normalized in known,
        )
        db.add(row)
        out.append({
            "entity_type": ent.entity_type,
            "masked": ent.masked,
            "previously_reported": ent.normalized in known,
        })
    audit.record(db, "citizen", "entity_added", case.id, meta={"type": payload.entity_type})
    result = analyse_case(db, case) if case.messages else None
    db.commit()
    return {"entities": out, "assessment": result}


@router.post("/{case_id}/evidence")
async def upload_evidence(
    case_id: str,
    kind: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    case = _get_case(db, case_id)
    if kind not in ("screenshot", "audio", "transcript", "qr"):
        raise HTTPException(422, "kind must be screenshot|audio|transcript|qr")
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(415, f"Unsupported file type: {content_type}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large")
    if not data:
        raise HTTPException(422, "Empty file")

    sha = hashlib.sha256(data).hexdigest()
    safe_name = f"{uuid.uuid4().hex}{ALLOWED_UPLOAD_TYPES[content_type]}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / safe_name).write_bytes(data)

    if kind == "screenshot":
        extraction = media.ocr_image(data)
        extracted_text = extraction.get("text", "")
    elif kind == "qr":
        extraction = media.decode_qr(data)
        extracted_text = " ".join(extraction.get("payloads", []))
        for upi in extraction.get("upi", []):
            if upi.get("payee_address"):
                extracted_text += f" {upi['payee_address']}"
    elif kind == "audio":
        extraction = media.transcribe_audio(data, file.filename or "audio")
        extracted_text = extraction.get("text", "")
    else:
        try:
            extracted_text = data.decode("utf-8", errors="replace")[:20000]
        except Exception:
            extracted_text = ""
        extraction = {"provider": "text", "text": extracted_text}

    ev = EvidenceFile(
        case_id=case.id,
        kind=kind,
        original_name=(file.filename or "upload")[:255],
        stored_name=safe_name,
        content_type=content_type,
        size_bytes=len(data),
        sha256=sha,
        extraction=extraction,
        extraction_provider=extraction.get("provider", ""),
    )
    db.add(ev)

    ents = extract_entities(extracted_text) if extracted_text else []
    known = reported_set(db, ents)
    for ent in ents:
        db.add(
            ExtractedEntity(
                case_id=case.id, entity_type=ent.entity_type, value=ent.value,
                normalized=ent.normalized, masked=ent.masked,
                source="ocr" if kind == "screenshot" else kind,
                previously_reported=ent.normalized in known,
            )
        )
    audit.record(
        db, "citizen", "evidence_uploaded", case.id,
        meta={"kind": kind, "sha256": sha, "provider": extraction.get("provider")},
    )
    result = None
    if kind == "transcript" and extracted_text:
        # Transcript lines become conversation messages: "Speaker: text" or raw lines.
        base = len(case.messages)
        lines = [l.strip() for l in extracted_text.splitlines() if l.strip()][:100]
        for i, line in enumerate(lines):
            m = re.match(r"^(caller|victim|scammer|officer|user)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)
            speaker = "victim" if m and m.group(1).lower() in ("victim", "user") else "caller"
            text = m.group(2) if m else line
            db.add(ConversationMessage(case_id=case.id, seq=base + i, speaker=speaker, text=text))
        db.flush()
        db.refresh(case)
        result = analyse_case(db, case)
    elif case.messages:
        result = analyse_case(db, case)
    db.commit()

    return {
        "evidence_id": ev.id,
        "sha256": sha,
        "provider": extraction.get("provider"),
        "simulated": extraction.get("provider") == "mock",
        "extraction": extraction,
        "entities_found": len(ents),
        "assessment": result,
    }


@router.get("/{case_id}/risk-timeline")
def risk_timeline(case_id: str, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    return {
        "case_id": case.id,
        "final_score": case.final_risk_score,
        "severity": case.severity,
        "points": [
            {
                "seq": m.seq,
                "speaker": m.speaker,
                "text": m.text,
                "timestamp": m.timestamp.isoformat(),
                "detected_signals": m.detected_signals,
                "risk_delta": m.risk_delta,
                "cumulative_risk": m.cumulative_risk,
            }
            for m in case.messages
        ],
    }


@router.get("/{case_id}/entities")
def case_entities(case_id: str, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    rows = db.query(ExtractedEntity).filter(ExtractedEntity.case_id == case.id).all()
    return [
        {
            "id": e.id,
            "entity_type": e.entity_type,
            "masked": e.masked,
            "source": e.source,
            "previously_reported": e.previously_reported,
        }
        for e in rows
    ]


@router.get("/{case_id}/assessment")
def latest_assessment(case_id: str, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    a = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.case_id == case.id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )
    if not a:
        raise HTTPException(404, "No analysis has been run for this case yet.")
    return {
        "score": a.score,
        "severity": a.severity,
        "confidence": a.confidence,
        "category": a.category,
        "stages_detected": a.stages_detected,
        "top_reasons": a.top_reasons,
        "recommended_actions": a.recommended_actions,
        "missing_evidence": a.missing_evidence,
        "false_positive_caution": a.false_positive_caution,
        "engine_version": a.engine_version,
        "timestamp": a.created_at.isoformat(),
    }


@router.post("/{case_id}/review")
def review_case(case_id: str, payload: ReviewCreate, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    db.add(
        ReviewDecision(
            case_id=case.id, reviewer="demo-investigator",
            decision=payload.decision, notes=payload.notes,
        )
    )
    prev = case.status
    case.status = "reviewed"
    audit.record(
        db, "demo-investigator", "status_changed", case.id,
        meta={"decision": payload.decision},
        previous_value=prev, new_value="reviewed",
    )
    db.commit()
    return {"status": "reviewed", "decision": payload.decision}


@router.post("/{case_id}/simulate-alert")
def simulate_alert(case_id: str, db: Session = Depends(get_db)):
    """SIMULATED escalation — no real bank, police or contact integration exists."""
    case = _get_case(db, case_id)
    audit.record(
        db, "citizen", "simulated_alert_initiated", case.id,
        meta={"channels": ["bank", "trusted_contact", "cybercrime_helpline_1930"], "simulated": True},
    )
    db.commit()
    return {
        "simulated": True,
        "message": "Simulated alerts recorded for bank, trusted contact and the 1930 helpline. "
                   "No real notification was sent — this is a prototype.",
    }
