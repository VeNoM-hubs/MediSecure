from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, require_roles
from app.core.rbac import Role
from app.models.appointment import Appointment
from app.models.audit import AuditLog
from app.models.user import DoctorProfile, PatientProfile, User
from app.schemas.common import AuditLogOut, StatsOut
from app.schemas.user import AccountStatusUpdate, PatientProfileOut
from app.services.audit import write_audit

router = APIRouter()


@router.get("/dashboard", response_model=StatsOut)
@router.get("/stats", response_model=StatsOut)
def system_stats(
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> StatsOut:
    patients = db.scalar(select(func.count()).select_from(PatientProfile)) or 0
    doctors = db.scalar(select(func.count()).select_from(DoctorProfile)) or 0
    appointments = db.scalar(select(func.count()).select_from(Appointment)) or 0
    active_users = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
    pending = (
        db.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == "pending")) or 0
    )
    completed = (
        db.scalar(select(func.count()).select_from(Appointment).where(Appointment.status == "completed")) or 0
    )
    cancelled = (
        db.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.status.in_(["cancelled", "rejected"]))
        )
        or 0
    )
    since = datetime.now(UTC) - timedelta(days=7)
    security_events = (
        db.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.created_at >= since,
                AuditLog.action.in_(
                    [
                        "auth.login_failed",
                        "auth.login_blocked",
                        "auth.password_change_failed",
                        "auth.register_failed",
                    ]
                ),
            )
        )
        or 0
    )
    return StatsOut(
        total_patients=patients,
        total_doctors=doctors,
        total_appointments=appointments,
        active_users=active_users,
        recent_security_events=security_events,
        pending_appointments=pending,
        completed_appointments=completed,
        cancelled_appointments=cancelled,
    )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
    limit: int = 100,
) -> list[AuditLogOut]:
    limit = min(max(limit, 1), 500)
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return [AuditLogOut.model_validate(r) for r in rows]


@router.get("/security-events", response_model=list[AuditLogOut])
def security_events(
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> list[AuditLogOut]:
    rows = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.action.in_(
                [
                    "auth.login_failed",
                    "auth.login_blocked",
                    "auth.password_change_failed",
                    "auth.register_failed",
                    "auth.password_change",
                ]
            )
        )
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    ).all()
    return [AuditLogOut.model_validate(r) for r in rows]


@router.patch("/users/{user_id}/status", response_model=dict)
def set_account_status(
    user_id: str,
    payload: AccountStatusUpdate,
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> dict:
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if target.id == admin.id and not payload.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")

    target.is_active = payload.is_active
    write_audit(
        db,
        action="admin.account_status",
        actor=admin,
        resource_type="user",
        resource_id=user_id,
        detail=f"is_active={payload.is_active}",
    )
    db.commit()
    # Never return password_hash
    return {
        "id": target.id,
        "email": target.email,
        "full_name": target.full_name,
        "role": target.role,
        "is_active": target.is_active,
    }


@router.get("/users", response_model=list[dict])
def admin_list_users(
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> list[dict]:
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/patients", response_model=list[PatientProfileOut])
def admin_list_patients(
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> list[PatientProfileOut]:
    profiles = db.scalars(select(PatientProfile).options(joinedload(PatientProfile.user))).all()
    return [
        PatientProfileOut(
            id=p.id,
            user_id=p.user.id,
            email=p.user.email,
            full_name=p.user.full_name,
            phone=p.user.phone,
            is_active=p.user.is_active,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            blood_type=p.blood_type,
            address=p.address,
            emergency_contact=p.emergency_contact,
        )
        for p in profiles
    ]
