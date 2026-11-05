from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.notification import Notification
from app.schemas.common import NotificationOut

router = APIRouter()


class UnreadCountOut(BaseModel):
    unread_count: int


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    db: DbSession,
    user: CurrentUser,
    unread_only: bool = False,
) -> list[NotificationOut]:
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    notes = db.scalars(stmt.order_by(Notification.created_at.desc())).all()
    return [NotificationOut.model_validate(n) for n in notes]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(db: DbSession, user: CurrentUser) -> UnreadCountOut:
    count = (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user.id, Notification.is_read.is_(False))
        )
        or 0
    )
    return UnreadCountOut(unread_count=count)


@router.post("/read-all", response_model=UnreadCountOut)
def mark_all_read(db: DbSession, user: CurrentUser) -> UnreadCountOut:
    notes = db.scalars(
        select(Notification).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    ).all()
    for note in notes:
        note.is_read = True
    db.commit()
    return UnreadCountOut(unread_count=0)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: str, db: DbSession, user: CurrentUser) -> NotificationOut:
    note = db.get(Notification, notification_id)
    if not note or note.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    note.is_read = True
    db.commit()
    db.refresh(note)
    return NotificationOut.model_validate(note)
