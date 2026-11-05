from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.common import NotificationOut

router = APIRouter()


@router.get("", response_model=list[NotificationOut])
def list_notifications(db: DbSession, user: CurrentUser) -> list[NotificationOut]:
    notes = db.scalars(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
    ).all()
    return [NotificationOut.model_validate(n) for n in notes]


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: str, db: DbSession, user: CurrentUser) -> NotificationOut:
    note = db.get(Notification, notification_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    note.is_read = True
    db.commit()
    db.refresh(note)
    return NotificationOut.model_validate(note)
