from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import PatientProfile, User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterPatientRequest,
    TokenResponse,
)
from app.schemas.user import UserPublic
from app.services.audit import write_audit
from app.services.lockout import clear_failed_logins, is_locked, register_failed_login
from app.services.tokens import issue_refresh_token, revoke_all_user_tokens, revoke_refresh_token, rotate_refresh_token

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _corr(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _token_response(db: DbSession, user: User) -> TokenResponse:
    settings = get_settings()
    access = create_access_token(user.id, {"role": user.role, "email": user.email})
    refresh = issue_refresh_token(db, user)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        role=Role(user.role),
        user_id=user.id,
        full_name=user.full_name,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_patient(payload: RegisterPatientRequest, request: Request, db: DbSession) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        write_audit(
            db,
            action="auth.register_failed",
            detail="Email already registered",
            ip_address=_client_ip(request),
            correlation_id=_corr(request),
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=Role.PATIENT.value,
        phone=payload.phone,
    )
    db.add(user)
    db.flush()
    db.add(
        PatientProfile(
            user_id=user.id,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
        )
    )
    write_audit(
        db,
        action="auth.register",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        ip_address=_client_ip(request),
        correlation_id=_corr(request),
    )
    tokens = _token_response(db, user)
    db.commit()
    return tokens


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    ip = _client_ip(request)
    corr = _corr(request)

    if not user or not verify_password(payload.password, user.password_hash):
        if user:
            register_failed_login(user)
        write_audit(
            db,
            action="auth.login_failed",
            actor=user,
            detail="Invalid credentials",
            ip_address=ip,
            correlation_id=corr,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if is_locked(user):
        write_audit(
            db,
            action="auth.login_blocked",
            actor=user,
            detail="Account temporarily locked",
            ip_address=ip,
            correlation_id=corr,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked due to failed attempts")

    if not user.is_active:
        write_audit(
            db,
            action="auth.login_blocked",
            actor=user,
            detail="Inactive account",
            ip_address=ip,
            correlation_id=corr,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    clear_failed_logins(user)
    write_audit(
        db,
        action="auth.login",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        ip_address=ip,
        correlation_id=corr,
    )
    tokens = _token_response(db, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: DbSession) -> TokenResponse:
    try:
        user, new_refresh = rotate_refresh_token(db, payload.refresh_token)
    except ValueError as exc:
        write_audit(
            db,
            action="auth.refresh_failed",
            detail=str(exc),
            ip_address=_client_ip(request),
            correlation_id=_corr(request),
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    settings = get_settings()
    access = create_access_token(user.id, {"role": user.role, "email": user.email})
    write_audit(
        db,
        action="auth.refresh",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        ip_address=_client_ip(request),
        correlation_id=_corr(request),
    )
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        role=Role(user.role),
        user_id=user.id,
        full_name=user.full_name,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    payload: LogoutRequest | None = None,
) -> MessageResponse:
    if payload and payload.refresh_token:
        revoke_refresh_token(db, payload.refresh_token)
    else:
        revoke_all_user_tokens(db, user.id)
    write_audit(
        db,
        action="auth.logout",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        ip_address=_client_ip(request),
        correlation_id=_corr(request),
    )
    db.commit()
    return MessageResponse(message="Logged out. Client must discard tokens.")


@router.get("/me", response_model=UserPublic)
def me(user: CurrentUser) -> User:
    return user


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> MessageResponse:
    if not verify_password(payload.current_password, user.password_hash):
        write_audit(
            db,
            action="auth.password_change_failed",
            actor=user,
            ip_address=_client_ip(request),
            correlation_id=_corr(request),
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.password_hash = hash_password(payload.new_password)
    revoke_all_user_tokens(db, user.id)
    write_audit(
        db,
        action="auth.password_change",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        ip_address=_client_ip(request),
        correlation_id=_corr(request),
    )
    db.commit()
    return MessageResponse(message="Password updated successfully")
