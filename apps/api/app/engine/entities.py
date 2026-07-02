"""Fraud-entity extraction, normalisation and masking."""
import re
from dataclasses import dataclass

PATTERNS: dict[str, list[re.Pattern]] = {
    "phone": [
        re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)"),
    ],
    "upi_id": [
        re.compile(
            r"\b[a-zA-Z0-9._-]{2,}@(?:ybl|ptyes|paytm|oksbi|okhdfcbank|okicici|okaxis|upi|apl|ibl|axl|fbl|jupiteraxis|barodampay)\b"
        ),
    ],
    "bank_account": [
        re.compile(r"\b(?:a/?c|account|acct|खाता)[\s.:no]*(\d{9,18})\b", re.IGNORECASE),
        re.compile(r"(?<!\d)\d{11,16}(?!\d)"),
    ],
    "ifsc": [re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")],
    "url": [re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)],
    "email": [re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")],
    "amount": [
        re.compile(r"(?:₹|rs\.?|inr)\s?[\d,]+(?:\.\d+)?", re.IGNORECASE),
        re.compile(r"[\d,]+\s?(?:lakh|lac|crore|लाख|करोड़)", re.IGNORECASE),
        re.compile(r"[\d,]+\s?(?:rupees|रुपये|रुपए)", re.IGNORECASE),
    ],
    "agency": [
        re.compile(
            r"\b(CBI|ED|RBI|TRAI|NCB|Interpol|Income Tax|Cyber ?Cell|Crime Branch|Enforcement Directorate|Customs|Supreme Court|High Court)\b",
            re.IGNORECASE,
        ),
        re.compile(r"(सीबीआई|ईडी|आरबीआई|पुलिस|कस्टम|साइबर सेल|प्रवर्तन निदेशालय)"),
    ],
    "remote_tool": [
        re.compile(r"\b(AnyDesk|TeamViewer|QuickSupport|RustDesk|AirDroid|एनीडेस्क|टीमव्यूअर)\b", re.IGNORECASE),
    ],
    "officer_name": [
        re.compile(
            r"\b(?:officer|inspector|acp|dcp|sub-?inspector|constable|sp|ips)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        ),
    ],
}

# Amounts and agencies are contextual facts, not identifiers to mask.
UNMASKED_TYPES = {"amount", "agency", "remote_tool"}


@dataclass(frozen=True)
class Entity:
    entity_type: str
    value: str
    normalized: str
    masked: str


def _normalise(entity_type: str, value: str) -> str:
    v = value.strip()
    if entity_type == "phone":
        digits = re.sub(r"\D", "", v)
        return digits[-10:] if len(digits) >= 10 else digits
    if entity_type in ("upi_id", "email", "url", "ifsc"):
        return v.lower().rstrip(".,)")
    if entity_type == "bank_account":
        return re.sub(r"\D", "", v)
    return v.lower()


def mask(entity_type: str, value: str) -> str:
    if entity_type in UNMASKED_TYPES:
        return value
    if entity_type == "phone":
        digits = re.sub(r"\D", "", value)[-10:]
        return f"+91-{digits[:2]}XXXXXX{digits[-2:]}" if len(digits) == 10 else "XXXXXXXX"
    if entity_type == "bank_account":
        digits = re.sub(r"\D", "", value)
        return "X" * max(0, len(digits) - 4) + digits[-4:]
    if entity_type == "upi_id" or entity_type == "email":
        name, _, domain = value.partition("@")
        keep = name[:2]
        return f"{keep}{'X' * max(1, len(name) - 2)}@{domain}"
    if entity_type == "url":
        m = re.match(r"(https?://[^/]+)", value)
        host = m.group(1) if m else value[:24]
        return host + "/…"
    if entity_type == "ifsc":
        return value[:4] + "0XXXXXX"
    if entity_type == "officer_name":
        parts = value.split()
        return " ".join(p[0] + "." for p in parts)
    return value[:2] + "…"


def extract_entities(text: str) -> list[Entity]:
    found: dict[tuple[str, str], Entity] = {}
    consumed: list[tuple[int, int]] = []

    def overlaps(span: tuple[int, int]) -> bool:
        return any(not (span[1] <= s or span[0] >= e) for s, e in consumed)

    # Priority order matters: UPI IDs would otherwise match as emails, and
    # phone numbers as bank accounts.
    order = [
        "url", "upi_id", "email", "ifsc", "phone", "bank_account",
        "amount", "agency", "remote_tool", "officer_name",
    ]
    for etype in order:
        for rx in PATTERNS[etype]:
            for m in rx.finditer(text):
                span = m.span()
                if overlaps(span):
                    continue
                value = m.group(1) if m.groups() else m.group(0)
                norm = _normalise(etype, value)
                if etype == "bank_account" and len(norm) < 9:
                    continue
                consumed.append(span)
                key = (etype, norm)
                if key not in found:
                    found[key] = Entity(etype, value.strip(), norm, mask(etype, value.strip()))
    return list(found.values())
