"""Append-only audit trail. The prototype exposes no delete path for audit rows."""
from sqlalchemy.orm import Session

from ..models import AuditLog


def record(
    db: Session,
    actor: str,
    action: str,
    case_id: str = "",
    meta: dict | None = None,
    previous_value: str = "",
    new_value: str = "",
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        case_id=case_id,
        meta=meta or {},
        previous_value=previous_value,
        new_value=new_value,
    )
    db.add(entry)
    return entry
