from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.rbac import Role
from app.models.appointment import Appointment
from app.models.user import DoctorProfile, PatientProfile, User


def get_patient_profile_or_404(db: Session, patient_profile_id: str) -> PatientProfile:
    profile = db.get(PatientProfile, patient_profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return profile


def get_doctor_profile_for_user(db: Session, user: User) -> DoctorProfile:
    profile = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")
    return profile


def get_patient_profile_for_user(db: Session, user: User) -> PatientProfile:
    profile = db.scalar(select(PatientProfile).where(PatientProfile.user_id == user.id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
    return profile


def doctor_has_patient_access(db: Session, doctor: DoctorProfile, patient_profile_id: str) -> bool:
    """Doctors may only access patients with an assigned (non-cancelled) appointment."""
    stmt = (
        select(Appointment.id)
        .where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_profile_id,
            Appointment.status != "cancelled",
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def assert_patient_self_or_admin(user: User, patient_profile: PatientProfile) -> None:
    if user.role == Role.ADMIN.value:
        return
    if user.role == Role.PATIENT.value and patient_profile.user_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to patient data")


def assert_doctor_authorized_for_patient(db: Session, user: User, patient_profile_id: str) -> DoctorProfile:
    if user.role != Role.DOCTOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor role required")
    doctor = get_doctor_profile_for_user(db, user)
    if not doctor_has_patient_access(db, doctor, patient_profile_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No authorized appointment relationship with this patient",
        )
    return doctor
