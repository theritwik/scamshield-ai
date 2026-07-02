"""Database models for cases, messages, evidence, entities, risk, graph, reports and audit."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), default="Untitled case")
    language: Mapped[str] = mapped_column(String(8), default="en")
    status: Mapped[str] = mapped_column(String(24), default="open")  # open|under_review|reviewed|closed
    source_type: Mapped[str] = mapped_column(String(24), default="text")  # text|call|sms|whatsapp|email
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    is_demo_seed: Mapped[bool] = mapped_column(Boolean, default=False)
    final_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[str] = mapped_column(String(12), default="Low")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    suspected_category: Mapped[str] = mapped_column(String(64), default="unclassified")
    payment_prevented: Mapped[bool] = mapped_column(Boolean, default=False)
    city: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="ConversationMessage.seq"
    )
    evidence: Mapped[list["EvidenceFile"]] = relationship(cascade="all, delete-orphan")
    entities: Mapped[list["ExtractedEntity"]] = relationship(cascade="all, delete-orphan")
    risk_events: Mapped[list["RiskEvent"]] = relationship(cascade="all, delete-orphan")
    reports: Mapped[list["EvidenceReport"]] = relationship(cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer, default=0)
    speaker: Mapped[str] = mapped_column(String(24), default="caller")  # caller|victim|system
    text: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)
    language: Mapped[str] = mapped_column(String(8), default="en")
    detected_signals: Mapped[list] = mapped_column(JSON, default=list)
    risk_delta: Mapped[float] = mapped_column(Float, default=0.0)
    cumulative_risk: Mapped[float] = mapped_column(Float, default=0.0)

    case: Mapped[Case] = relationship(back_populates="messages")


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    kind: Mapped[str] = mapped_column(String(24))  # screenshot|audio|transcript|qr
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64))
    extraction: Mapped[dict] = mapped_column(JSON, default=dict)  # OCR text / QR payload / transcript
    extraction_provider: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[str] = mapped_column(String(255))
    normalized: Mapped[str] = mapped_column(String(255), index=True)
    masked: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(32), default="message")  # message|ocr|qr|manual
    first_seen_seq: Mapped[int] = mapped_column(Integer, default=0)
    previously_reported: Mapped[bool] = mapped_column(Boolean, default=False)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    message_id: Mapped[str] = mapped_column(String(32), default="")
    seq: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String(48))
    signal_id: Mapped[str] = mapped_column(String(48))
    label: Mapped[str] = mapped_column(String(128))
    weight: Mapped[float] = mapped_column(Float, default=0.0)
    kind: Mapped[str] = mapped_column(String(24), default="signal")  # signal|sequence_bonus|entity_reputation
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(12))
    confidence: Mapped[float] = mapped_column(Float)
    category: Mapped[str] = mapped_column(String(64))
    stages_detected: Mapped[list] = mapped_column(JSON, default=list)
    top_reasons: Mapped[list] = mapped_column(JSON, default=list)
    recommended_actions: Mapped[list] = mapped_column(JSON, default=list)
    missing_evidence: Mapped[list] = mapped_column(JSON, default=list)
    false_positive_caution: Mapped[str] = mapped_column(Text, default="")
    engine_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class FraudGraphNode(Base):
    __tablename__ = "fraud_graph_nodes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # type:normalized_value
    node_type: Mapped[str] = mapped_column(String(32), index=True)
    label: Mapped[str] = mapped_column(String(255))
    masked_label: Mapped[str] = mapped_column(String(255))
    risk: Mapped[float] = mapped_column(Float, default=0.0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class FraudGraphEdge(Base):
    __tablename__ = "fraud_graph_edges"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    source: Mapped[str] = mapped_column(ForeignKey("fraud_graph_nodes.id"), index=True)
    target: Mapped[str] = mapped_column(ForeignKey("fraud_graph_nodes.id"), index=True)
    relation: Mapped[str] = mapped_column(String(48))
    case_id: Mapped[str] = mapped_column(String(32), default="")


class EvidenceReport(Base):
    __tablename__ = "evidence_reports"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    engine_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)
    actor: Mapped[str] = mapped_column(String(64), default="citizen")
    action: Mapped[str] = mapped_column(String(64), index=True)
    case_id: Mapped[str] = mapped_column(String(32), default="", index=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    previous_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"), index=True)
    reviewer: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(24))  # confirmed_scam|likely_scam|not_scam|needs_more_info
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class ReportedEntity(Base):
    """Synthetic registry of previously reported entities used for reputation scoring."""

    __tablename__ = "reported_entities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    normalized: Mapped[str] = mapped_column(String(255), index=True)
    report_count: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str] = mapped_column(String(255), default="")
