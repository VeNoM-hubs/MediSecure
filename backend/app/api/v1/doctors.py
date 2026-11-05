from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.rbac import Role
from app.core.security import hash_password
from app.models.specialization import Specialization
from app.models.user import DoctorProfile, User
from app.schemas.appointment import SlotCreate
from app.schemas.user import DoctorCreate, DoctorOut
from app.services.access import get_doctor_profile_for_user
from app.services.audit import write_audit

router = APIRouter()


def _to_out(profile: DoctorProfile) -> DoctorOut:
    user = profile.user
    return DoctorOut(
        id=profile.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        specialization_id=profile.specialization_id,
        specialization_name=profile.specialization.name if profile.specialization else None,
        license_number=profile.license_number,
        qualifications=profile.qualifications,
        bio=profile.bio,
        years_experience=profile.years_experience,
        availability_notes=profile.availability_notes,
    )


@router.get("", response_model=list[DoctorOut])
def list_doctors(db: DbSession, user: CurrentUser) -> list[DoctorOut]:
    # Patients, doctors, and admins can view available doctors
    if user.role not in {Role.PATIENT.value, Role.DOCTOR.value, Role.ADMIN.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    stmt = (
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user), joinedload(DoctorProfile.specialization))
        .join(User, DoctorProfile.user_id == User.id)
        .where(User.is_active.is_(True))
    )
    profiles = db.scalars(stmt).unique().all()
    return [_to_out(p) for p in profiles]


@router.get("/me", response_model=DoctorOut)
def my_doctor_profile(
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> DoctorOut:
    profile = db.scalar(
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user), joinedload(DoctorProfile.specialization))
        .where(DoctorProfile.user_id == user.id)
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return _to_out(profile)


@router.get("/me/slots", response_model=list[dict])
def my_slots(
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> list[dict]:
    from datetime import UTC, datetime

    from app.models.appointment_slot import AppointmentSlot

    doctor = get_doctor_profile_for_user(db, user)
    slots = db.scalars(
        select(AppointmentSlot)
        .where(AppointmentSlot.doctor_id == doctor.id, AppointmentSlot.starts_at >= datetime.now(UTC))
        .order_by(AppointmentSlot.starts_at.asc())
    ).all()
    return [
        {
            "id": s.id,
            "doctor_id": s.doctor_id,
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
            "is_booked": s.is_booked,
        }
        for s in slots
    ]


@router.post("/me/slots", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_slot(
    payload: SlotCreate,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> dict:
    from datetime import UTC, datetime, timedelta

    from app.models.appointment_slot import AppointmentSlot

    doctor = get_doctor_profile_for_user(db, user)
    starts_at = payload.starts_at
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=UTC)
    if starts_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create slots in the past")

    ends_at = payload.ends_at or (starts_at + timedelta(minutes=30))
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=UTC)
    if ends_at <= starts_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ends_at must be after starts_at")

    existing = db.scalar(
        select(AppointmentSlot.id).where(
            AppointmentSlot.doctor_id == doctor.id,
            AppointmentSlot.starts_at == starts_at,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot already exists at this time")

    slot = AppointmentSlot(doctor_id=doctor.id, starts_at=starts_at, ends_at=ends_at, is_booked=False)
    db.add(slot)
    write_audit(
        db,
        action="slot.create",
        actor=user,
        resource_type="appointment_slot",
        resource_id=slot.id,
        correlation_id=getattr(request.state, "request_id", None),
    )
    db.commit()
    db.refresh(slot)
    return {
        "id": slot.id,
        "doctor_id": slot.doctor_id,
        "starts_at": slot.starts_at.isoformat(),
        "ends_at": slot.ends_at.isoformat(),
        "is_booked": slot.is_booked,
    }


@router.delete("/me/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slot(
    slot_id: str,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> None:
    from app.models.appointment_slot import AppointmentSlot
    from app.services.audit import write_audit

    doctor = get_doctor_profile_for_user(db, user)
    slot = db.get(AppointmentSlot, slot_id)
    if not slot or slot.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a booked slot")
    write_audit(
        db,
        action="slot.delete",
        actor=user,
        resource_type="appointment_slot",
        resource_id=slot_id,
        correlation_id=getattr(request.state, "request_id", None),
    )
    db.delete(slot)
    db.commit()


@router.get("/{doctor_id}/availability", response_model=list[dict])
def doctor_availability(doctor_id: str, db: DbSession, user: CurrentUser) -> list[dict]:
    from datetime import UTC, datetime

    from app.models.appointment_slot import AppointmentSlot

    profile = db.get(DoctorProfile, doctor_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    now = datetime.now(UTC)
    slots = db.scalars(
        select(AppointmentSlot)
        .where(
            AppointmentSlot.doctor_id == doctor_id,
            AppointmentSlot.is_booked.is_(False),
            AppointmentSlot.starts_at >= now,
        )
        .order_by(AppointmentSlot.starts_at.asc())
    ).all()
    return [
        {
            "id": s.id,
            "doctor_id": s.doctor_id,
            "starts_at": s.starts_at.isoformat(),
            "ends_at": s.ends_at.isoformat(),
            "is_booked": s.is_booked,
        }
        for s in slots
    ]


@router.get("/me/schedule", response_model=list[dict])
def my_schedule(
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> list[dict]:
    from app.models.appointment import Appointment

    doctor = get_doctor_profile_for_user(db, user)
    appts = db.scalars(
        select(Appointment)
        .where(Appointment.doctor_id == doctor.id, Appointment.status != "cancelled")
        .order_by(Appointment.scheduled_at.asc())
    ).all()
    return [
        {
            "id": a.id,
            "scheduled_at": a.scheduled_at.isoformat(),
            "status": a.status,
            "patient_id": a.patient_id,
            "reason": a.reason,
        }
        for a in appts
    ]


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, db: DbSession, user: CurrentUser) -> DoctorOut:
    profile = db.scalar(
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user), joinedload(DoctorProfile.specialization))
        .where(DoctorProfile.id == doctor_id)
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return _to_out(profile)


@router.post("", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
def create_doctor(
    payload: DoctorCreate,
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> DoctorOut:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if payload.specialization_id and not db.get(Specialization, payload.specialization_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid specialization")

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=Role.DOCTOR.value,
        phone=payload.phone,
    )
    db.add(user)
    db.flush()
    profile = DoctorProfile(
        user_id=user.id,
        specialization_id=payload.specialization_id,
        license_number=payload.license_number,
        qualifications=payload.qualifications,
        bio=payload.bio,
        years_experience=payload.years_experience,
        availability_notes=payload.availability_notes,
    )
    db.add(profile)
    write_audit(
        db,
        action="doctor.create",
        actor=admin,
        resource_type="doctor",
        resource_id=profile.id,
        detail=f"Created doctor {user.email}",
    )
    db.commit()
    profile = db.scalar(
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user), joinedload(DoctorProfile.specialization))
        .where(DoctorProfile.id == profile.id)
    )
    assert profile is not None
    return _to_out(profile)
