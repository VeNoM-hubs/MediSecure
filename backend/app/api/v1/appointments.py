from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.rbac import Role
from app.models.appointment import Appointment
from app.models.appointment_slot import AppointmentSlot
from app.models.notification import Notification
from app.models.user import DoctorProfile, PatientProfile, User
from app.schemas.appointment import AppointmentCreate, AppointmentOut, AppointmentStatusUpdate
from app.services.access import get_doctor_profile_for_user, get_patient_profile_for_user
from app.services.audit import write_audit

router = APIRouter()

CANCELABLE = {"scheduled", "confirmed", "pending"}
ALLOWED_TRANSITIONS = {
    "scheduled": {"confirmed", "cancelled", "rejected", "completed", "no_show"},
    "pending": {"confirmed", "cancelled", "rejected"},
    "confirmed": {"completed", "cancelled", "no_show"},
    "completed": set(),
    "cancelled": set(),
    "rejected": set(),
    "no_show": set(),
}


def _corr(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _to_out(appt: Appointment) -> AppointmentOut:
    patient_name = appt.patient.user.full_name if appt.patient and appt.patient.user else None
    doctor_name = appt.doctor.user.full_name if appt.doctor and appt.doctor.user else None
    return AppointmentOut(
        id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        scheduled_at=appt.scheduled_at,
        status=appt.status,
        reason=appt.reason,
        consultation_notes=appt.consultation_notes,
        patient_name=patient_name,
        doctor_name=doctor_name,
        created_at=appt.created_at,
    )


def _load_stmt():
    return select(Appointment).options(
        joinedload(Appointment.patient).joinedload(PatientProfile.user),
        joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
    )


def _assert_no_double_booking(db: DbSession, doctor_id: str, scheduled_at: datetime) -> None:
    window_start = scheduled_at - timedelta(minutes=29)
    window_end = scheduled_at + timedelta(minutes=29)
    conflict = db.scalar(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status.notin_(["cancelled", "rejected"]),
            Appointment.scheduled_at >= window_start,
            Appointment.scheduled_at <= window_end,
        )
    )
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Doctor already booked near this time")


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreate,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.PATIENT)),
) -> AppointmentOut:
    patient = get_patient_profile_for_user(db, user)
    doctor = db.scalar(
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user))
        .where(DoctorProfile.id == payload.doctor_id)
    )
    if not doctor or not doctor.user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    if payload.scheduled_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book in the past")

    slot = None
    if payload.slot_id:
        slot = db.get(AppointmentSlot, payload.slot_id)
        if not slot or slot.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid appointment slot")
        if slot.is_booked:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot already booked")
        if slot.starts_at != payload.scheduled_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot time mismatch")

    _assert_no_double_booking(db, doctor.id, payload.scheduled_at)

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=payload.scheduled_at,
        status="pending",
        reason=payload.reason,
    )
    db.add(appt)
    db.flush()
    if slot:
        slot.is_booked = True

    db.add(
        Notification(
            user_id=doctor.user_id,
            title="New appointment request",
            message=f"{user.full_name} requested an appointment for {payload.scheduled_at.isoformat()}",
            category="appointment",
        )
    )
    write_audit(
        db,
        action="appointment.create",
        actor=user,
        resource_type="appointment",
        resource_id=appt.id,
        correlation_id=_corr(request),
    )
    db.commit()
    appt = db.scalar(_load_stmt().where(Appointment.id == appt.id))
    assert appt is not None
    return _to_out(appt)


@router.get("", response_model=list[AppointmentOut])
@router.get("/mine", response_model=list[AppointmentOut])
def list_appointments(db: DbSession, user: CurrentUser) -> list[AppointmentOut]:
    if user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        stmt = _load_stmt().where(Appointment.patient_id == patient.id)
    elif user.role == Role.DOCTOR.value:
        doctor = get_doctor_profile_for_user(db, user)
        stmt = _load_stmt().where(Appointment.doctor_id == doctor.id)
    elif user.role == Role.ADMIN.value:
        stmt = _load_stmt()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    appts = db.scalars(stmt.order_by(Appointment.scheduled_at.desc())).unique().all()
    return [_to_out(a) for a in appts]


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: str, db: DbSession, user: CurrentUser) -> AppointmentOut:
    appt = db.scalar(_load_stmt().where(Appointment.id == appointment_id))
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if user.role == Role.ADMIN.value:
        return _to_out(appt)
    if user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        if appt.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif user.role == Role.DOCTOR.value:
        doctor = get_doctor_profile_for_user(db, user)
        if appt.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _to_out(appt)


@router.delete("/{appointment_id}", response_model=AppointmentOut)
@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: str,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.PATIENT, Role.ADMIN)),
) -> AppointmentOut:
    appt = db.scalar(_load_stmt().where(Appointment.id == appointment_id))
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        if appt.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot cancel another patient's appointment")

    if appt.status not in CANCELABLE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment cannot be cancelled")

    appt.status = "cancelled"
    write_audit(
        db,
        action="appointment.cancel",
        actor=user,
        resource_type="appointment",
        resource_id=appt.id,
        correlation_id=_corr(request),
    )
    db.commit()
    db.refresh(appt)
    return _to_out(appt)


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def update_status(
    appointment_id: str,
    payload: AppointmentStatusUpdate,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR, Role.ADMIN)),
) -> AppointmentOut:
    appt = db.scalar(_load_stmt().where(Appointment.id == appointment_id))
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if user.role == Role.DOCTOR.value:
        doctor = get_doctor_profile_for_user(db, user)
        if appt.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your appointment")

    allowed = ALLOWED_TRANSITIONS.get(appt.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transition from {appt.status} to {payload.status}",
        )

    appt.status = payload.status
    if payload.consultation_notes is not None:
        appt.consultation_notes = payload.consultation_notes

    # Notify patient of status change
    patient_user_id = appt.patient.user_id if appt.patient else None
    if patient_user_id:
        db.add(
            Notification(
                user_id=patient_user_id,
                title=f"Appointment {payload.status}",
                message=f"Your appointment status is now {payload.status}.",
                category="appointment",
            )
        )

    write_audit(
        db,
        action="appointment.status_update",
        actor=user,
        resource_type="appointment",
        resource_id=appt.id,
        detail=f"status={payload.status}",
        correlation_id=_corr(request),
    )
    db.commit()
    db.refresh(appt)
    return _to_out(appt)
