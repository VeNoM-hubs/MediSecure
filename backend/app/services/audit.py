from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def write_audit(
    db: Session,
    *,
    action: str,
    actor: User | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    correlation_id: str | None = None,
    success: bool = True,
) -> AuditLog:
    # Never log passwords, tokens, or full medical content via callers.
    entry = AuditLog(
        actor_user_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        actor_role=actor.role if actor else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
        correlation_id=correlation_id,
        success=success,
    )
    db.add(entry)
    db.flush()
    return entry
