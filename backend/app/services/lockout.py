from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.models.user import User


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def is_locked(user: User) -> bool:
    if user.locked_until and _aware(user.locked_until) > datetime.now(UTC):
        return True
    return False


def register_failed_login(user: User) -> None:
    settings = get_settings()
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
    if user.failed_login_attempts >= settings.login_max_failures:
        user.locked_until = datetime.now(UTC) + timedelta(minutes=settings.login_lockout_minutes)


def clear_failed_logins(user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
