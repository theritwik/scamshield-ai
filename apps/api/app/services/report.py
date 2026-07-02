"""EvidenceChain PDF report generation with ReportLab."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from ..config import ENGINE_VERSION, REPORT_DIR
from ..models import (
    AuditLog,
    Case,
    EvidenceFile,
    ExtractedEntity,
    FraudGraphEdge,
    RiskAssessment,
)

NAVY = colors.HexColor("#0b1f3a")
RED = colors.HexColor("#c0392b")
AMBER = colors.HexColor("#b7791f")
GREEN = colors.HexColor("#1e7e34")

SEVERITY_COLORS = {"Critical": RED, "High": RED, "Medium": AMBER, "Low": GREEN}


def _esc(text: str) -> str:
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def generate_pdf(db: Session, case: Case) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"evidence-report-{case.case_number}.pdf"

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1x", parent=styles["Heading1"], textColor=NAVY, fontSize=17)
    h2 = ParagraphStyle("h2x", parent=styles["Heading2"], textColor=NAVY, fontSize=12, spaceBefore=12)
    body = ParagraphStyle("bodyx", parent=styles["BodyText"], fontSize=9, leading=13)
    small = ParagraphStyle("smallx", parent=styles["BodyText"], fontSize=7.5, textColor=colors.grey, leading=10)

    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.case_id == case.id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )
    entities = db.query(ExtractedEntity).filter(ExtractedEntity.case_id == case.id).all()
    evidence = db.query(EvidenceFile).filter(EvidenceFile.case_id == case.id).all()
    edges = db.query(FraudGraphEdge).filter(FraudGraphEdge.case_id == case.id).all()
    audit = (
        db.query(AuditLog)
        .filter(AuditLog.case_id == case.id)
        .order_by(AuditLog.timestamp)
        .all()
    )

    story = []
    story.append(Paragraph("SCAMSHIELD AI — EVIDENCECHAIN REPORT", h1))
    story.append(Paragraph(
        "Digital Arrest Scam Defence &amp; Fraud Intelligence — auditable case record", small))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", color=NAVY, thickness=1.2))
    story.append(Spacer(1, 8))

    sev_color = SEVERITY_COLORS.get(case.severity, GREEN)
    meta_rows = [
        ["Case ID", case.case_number, "Created (UTC)", case.created_at.strftime("%Y-%m-%d %H:%M:%S")],
        ["Report generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
         "Engine version", ENGINE_VERSION],
        ["Consent", "Recorded" if case.consent_given else "NOT RECORDED",
         "Language", "Hindi" if case.language == "hi" else "English"],
        ["Final risk score", f"{case.final_risk_score:.0f} / 100",
         "Severity", case.severity],
        ["Confidence", f"{case.confidence:.0%}", "Suspected category",
         case.suspected_category.replace("_", " ")],
    ]
    t = Table(meta_rows, colWidths=[32 * mm, 55 * mm, 32 * mm, 55 * mm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (3, 3), (3, 3), sev_color),
        ("FONTNAME", (3, 3), (3, 3), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0dc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef2f7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Paragraph("1. Case summary", h2))
    story.append(Paragraph(_esc(case.title), body))
    if assessment:
        story.append(Paragraph(
            f"The sequence-aware coercion engine assessed this interaction as "
            f"<b>{_esc(assessment.severity)}</b> risk ({assessment.score:.0f}/100) in category "
            f"<b>{_esc(assessment.category.replace('_', ' '))}</b>. "
            f"{len(assessment.stages_detected)} coercion stage(s) were detected.", body))

    if assessment and assessment.stages_detected:
        story.append(Paragraph("2. Detected coercion sequence", h2))
        rows = [["#", "Stage", "Detected as"]]
        for s in assessment.stages_detected:
            rows.append([str(s.get("order", "")), _esc(s.get("label", "")), _esc(s.get("stage", ""))])
        st = Table(rows, colWidths=[10 * mm, 90 * mm, 74 * mm])
        st.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0dc")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(st)

    story.append(Paragraph("3. Risk timeline and transcript excerpts", h2))
    rows = [["#", "Speaker", "Excerpt", "Signals", "Δ", "Cumulative"]]
    for m in case.messages:
        sig = ", ".join(
            s.get("label", "") for s in (m.detected_signals or []) if s.get("kind") == "signal"
        )[:120]
        rows.append([
            str(m.seq + 1), _esc(m.speaker),
            Paragraph(_esc(m.text[:220]), small),
            Paragraph(_esc(sig or "—"), small),
            f"+{m.risk_delta:.0f}" if m.risk_delta > 0 else "0",
            f"{m.cumulative_risk:.0f}%",
        ])
    mt = Table(rows, colWidths=[8 * mm, 18 * mm, 72 * mm, 46 * mm, 12 * mm, 18 * mm])
    mt.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0dc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(mt)

    story.append(Paragraph("4. Extracted entities (masked)", h2))
    if entities:
        rows = [["Type", "Masked value", "Source", "Previously reported"]]
        for e in entities:
            rows.append([
                e.entity_type.replace("_", " "), _esc(e.masked), e.source,
                "YES" if e.previously_reported else "no",
            ])
        et = Table(rows, colWidths=[30 * mm, 70 * mm, 30 * mm, 44 * mm])
        et.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0dc")),
        ]))
        story.append(et)
    else:
        story.append(Paragraph("No entities were extracted for this case.", body))

    story.append(Paragraph("5. Evidence inventory (SHA-256 integrity hashes)", h2))
    if evidence:
        rows = [["File", "Type", "Size", "SHA-256"]]
        for ev in evidence:
            rows.append([
                _esc(ev.original_name[:36]), ev.kind, f"{ev.size_bytes} B",
                Paragraph(f"<font size=6>{ev.sha256}</font>", small),
            ])
        evt = Table(rows, colWidths=[48 * mm, 20 * mm, 20 * mm, 86 * mm])
        evt.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0dc")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(evt)
    else:
        story.append(Paragraph(
            "No files were uploaded. The conversation record above is the primary evidence.", body))

    story.append(Paragraph("6. Fraud-graph relationships", h2))
    if edges:
        for e in edges[:12]:
            story.append(Paragraph(
                f"• {_esc(e.source)} —[{_esc(e.relation)}]→ {_esc(e.target)}", small))
    else:
        story.append(Paragraph("No graph relationships recorded for this case.", body))

    if assessment:
        story.append(Paragraph("7. Recommended next actions", h2))
        for a in assessment.recommended_actions:
            story.append(Paragraph(f"• {_esc(a)}", body))

    story.append(Paragraph("8. Audit trail", h2))
    rows = [["Timestamp (UTC)", "Actor", "Action"]]
    for a in audit[-15:]:
        rows.append([a.timestamp.strftime("%Y-%m-%d %H:%M:%S"), a.actor, a.action])
    at = Table(rows, colWidths=[45 * mm, 35 * mm, 94 * mm])
    at.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d0dc")),
    ]))
    story.append(at)

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.grey, thickness=0.6))
    story.append(Paragraph(
        "PRIVACY: Sensitive identifiers are masked in this report. Original evidence files are "
        "hashed (SHA-256) and never modified. This case uses consent-based analysis; raw evidence "
        "is retained only as long as necessary for the complaint.", small))
    story.append(Paragraph(
        "HUMAN REVIEW: This is an automated decision-support assessment produced by a rule-based, "
        "sequence-aware engine. It is not a legal determination of fraud or guilt and requires "
        "verification by an authorised human investigator. Entities are 'suspected' or "
        "'reported', never 'guilty'.", small))
    story.append(Paragraph(
        "PROTOTYPE: ScamShield AI is a hackathon prototype. Bank, police and telecom "
        "integrations shown in the product are simulated.", small))

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"ScamShield AI Evidence Report {case.case_number}",
    )
    doc.build(story)
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
