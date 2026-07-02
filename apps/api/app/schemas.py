"""Pydantic request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CaseCreate(BaseModel):
    title: str = Field(default="Untitled case", max_length=200)
    language: str = Field(default="en", pattern="^(en|hi)$")
    source_type: str = Field(default="text", pattern="^(text|call|sms|whatsapp|email)$")
    consent_given: bool = False
    city: str = Field(default="", max_length=64)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return v.strip()[:200] or "Untitled case"


class MessageCreate(BaseModel):
    speaker: str = Field(default="caller", pattern="^(caller|victim|system)$")
    text: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="en", pattern="^(en|hi)$")


class MessagesBulkCreate(BaseModel):
    messages: list[MessageCreate] = Field(min_length=1, max_length=200)


class ManualEntity(BaseModel):
    entity_type: str = Field(pattern="^(phone|upi_id|bank_account|url|email|ifsc)$")
    value: str = Field(min_length=3, max_length=255)


class ReviewCreate(BaseModel):
    decision: str = Field(pattern="^(confirmed_scam|likely_scam|not_scam|needs_more_info)$")
    notes: str = Field(default="", max_length=2000)


class MessageOut(BaseModel):
    id: str
    seq: int
    speaker: str
    text: str
    timestamp: datetime
    detected_signals: list
    risk_delta: float
    cumulative_risk: float

    model_config = {"from_attributes": True}


class EntityOut(BaseModel):
    id: str
    entity_type: str
    masked: str
    source: str
    previously_reported: bool

    model_config = {"from_attributes": True}


class CaseOut(BaseModel):
    id: str
    case_number: str
    title: str
    language: str
    status: str
    source_type: str
    consent_given: bool
    final_risk_score: float
    severity: str
    confidence: float
    suspected_category: str
    payment_prevented: bool
    city: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailOut(CaseOut):
    messages: list[MessageOut] = []
    entities: list[EntityOut] = []
