from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.rbac import Role
from app.models.user import PatientProfile, User
from app.schemas.user import PatientProfileOut, PatientProfileUpdate
from app.services.access import (
    assert_doctor_authorized_for_patient,
    assert_patient_self_or_admin,
    get_patient_profile_for_user,
    get_patient_profile_or_404,
)
from app.services.audit import write_audit

router = APIRouter()


def _to_out(profile: PatientProfile) -> PatientProfileOut:
    user = profile.user
    return PatientProfileOut(
        id=profile.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        blood_type=profile.blood_type,
        address=profile.address,
        emergency_contact=profile.emergency_contact,
    )


@router.get("/me", response_model=PatientProfileOut)
def get_my_profile(
    db: DbSession,
    user: User = Depends(require_roles(Role.PATIENT)),
) -> PatientProfileOut:
    profile = get_patient_profile_for_user(db, user)
    return _to_out(profile)


@router.put("/me", response_model=PatientProfileOut)
def update_my_profile(
    payload: PatientProfileUpdate,
    db: DbSession,
    user: User = Depends(require_roles(Role.PATIENT)),
) -> PatientProfileOut:
    profile = get_patient_profile_for_user(db, user)
    data = payload.model_dump(exclude_unset=True)
    if "full_name" in data and data["full_name"]:
        user.full_name = data.pop("full_name")
    if "phone" in data:
        user.phone = data.pop("phone")
    for key, value in data.items():
        setattr(profile, key, value)
    write_audit(db, action="patient.profile_update", actor=user, resource_type="patient", resource_id=profile.id)
    db.commit()
    db.refresh(profile)
    return _to_out(profile)


@router.get("/{patient_id}", response_model=PatientProfileOut)
def get_patient(patient_id: str, db: DbSession, user: CurrentUser) -> PatientProfileOut:
    profile = db.scalar(
        select(PatientProfile)
        .options(joinedload(PatientProfile.user))
        .where(PatientProfile.id == patient_id)
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if user.role == Role.ADMIN.value:
        pass
    elif user.role == Role.PATIENT.value:
        assert_patient_self_or_admin(user, profile)
    elif user.role == Role.DOCTOR.value:
        assert_doctor_authorized_for_patient(db, user, patient_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    write_audit(
        db,
        action="patient.read",
        actor=user,
        resource_type="patient",
        resource_id=patient_id,
    )
    db.commit()
    return _to_out(profile)


@router.get("", response_model=list[PatientProfileOut])
def list_patients(
    db: DbSession,
    user: User = Depends(require_roles(Role.ADMIN)),
) -> list[PatientProfileOut]:
    profiles = db.scalars(select(PatientProfile).options(joinedload(PatientProfile.user))).all()
    return [_to_out(p) for p in profiles]
