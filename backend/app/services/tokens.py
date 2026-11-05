from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_refresh_token, hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User


def issue_refresh_token(db: Session, user: User) -> str:
    settings = get_settings()
    raw = generate_refresh_token()
    row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        revoked=False,
    )
    db.add(row)
    db.flush()
    return raw


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str]:
    token_hash = hash_token(raw_token)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if not row or row.revoked or _aware(row.expires_at) < datetime.now(UTC):
        raise ValueError("Invalid or expired refresh token")

    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise ValueError("User inactive or not found")

    row.revoked = True
    new_raw = issue_refresh_token(db, user)
    new_row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(new_raw)))
    if new_row:
        row.replaced_by = new_row.id
    db.flush()
    return user, new_raw


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if row and not row.revoked:
        row.revoked = True
        db.flush()


def revoke_all_user_tokens(db: Session, user_id: str) -> None:
    rows = db.scalars(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
    ).all()
    for row in rows:
        row.revoked = True
    db.flush()
