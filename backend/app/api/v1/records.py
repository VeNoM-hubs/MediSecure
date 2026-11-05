from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.rbac import Role
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordOut
from app.services.access import (
    assert_doctor_authorized_for_patient,
    get_patient_profile_for_user,
    get_patient_profile_or_404,
)
from app.services.audit import write_audit

router = APIRouter()


@router.get("/mine", response_model=list[MedicalRecordOut])
def my_records(
    db: DbSession,
    user: User = Depends(require_roles(Role.PATIENT)),
) -> list[MedicalRecordOut]:
    patient = get_patient_profile_for_user(db, user)
    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient.id)
        .order_by(MedicalRecord.record_date.desc())
    ).all()
    return [MedicalRecordOut.model_validate(r) for r in records]


@router.get("/patient/{patient_id}", response_model=list[MedicalRecordOut])
def records_for_patient(patient_id: str, db: DbSession, user: CurrentUser) -> list[MedicalRecordOut]:
    get_patient_profile_or_404(db, patient_id)

    if user.role == Role.ADMIN.value:
        pass
    elif user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        if patient.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other patient records")
    elif user.role == Role.DOCTOR.value:
        assert_doctor_authorized_for_patient(db, user, patient_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    records = db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.record_date.desc())
    ).all()
    write_audit(db, action="records.list", actor=user, resource_type="patient", resource_id=patient_id)
    db.commit()
    return [MedicalRecordOut.model_validate(r) for r in records]


@router.post("", response_model=MedicalRecordOut, status_code=status.HTTP_201_CREATED)
def add_record(
    payload: MedicalRecordCreate,
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> MedicalRecordOut:
    doctor = assert_doctor_authorized_for_patient(db, user, payload.patient_id)
    record = MedicalRecord(
        patient_id=payload.patient_id,
        created_by_doctor_id=doctor.id,
        title=payload.title,
        diagnosis=payload.diagnosis,
        treatment=payload.treatment,
        notes=payload.notes,
    )
    db.add(record)
    write_audit(
        db,
        action="records.create",
        actor=user,
        resource_type="medical_record",
        resource_id=record.id,
    )
    db.commit()
    db.refresh(record)
    return MedicalRecordOut.model_validate(record)
