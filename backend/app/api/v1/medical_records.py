from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.rbac import Role
from app.models.medical_record import MedicalRecord
from app.models.notification import Notification
from app.models.user import PatientProfile, User
from app.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordMetaOut,
    MedicalRecordOut,
    MedicalRecordUpdate,
)
from app.services.access import (
    assert_doctor_authorized_for_patient,
    get_patient_profile_for_user,
    get_patient_profile_or_404,
)
from app.services.audit import write_audit

router = APIRouter()


def _corr(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@router.get("/meta", response_model=list[MedicalRecordMetaOut])
def list_record_metadata(
    request: Request,
    db: DbSession,
    admin: User = Depends(require_roles(Role.ADMIN)),
) -> list[MedicalRecordMetaOut]:
    """Admin metadata view — clinical fields intentionally omitted."""
    records = db.scalars(select(MedicalRecord).order_by(MedicalRecord.record_date.desc()).limit(200)).all()
    write_audit(
        db,
        action="records.meta_list",
        actor=admin,
        resource_type="medical_record",
        correlation_id=_corr(request),
        detail="Admin viewed record metadata only",
    )
    db.commit()
    return [MedicalRecordMetaOut.model_validate(r) for r in records]


@router.get("", response_model=list[MedicalRecordOut])
@router.get("/mine", response_model=list[MedicalRecordOut])
def list_my_records(
    request: Request,
    db: DbSession,
    user: CurrentUser,
) -> list[MedicalRecordOut]:
    if user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        records = db.scalars(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient.id)
            .order_by(MedicalRecord.record_date.desc())
        ).all()
    elif user.role == Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins must use /medical-records/meta for non-clinical metadata",
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Use patient-scoped endpoint")

    write_audit(
        db,
        action="records.list",
        actor=user,
        resource_type="medical_record",
        correlation_id=_corr(request),
    )
    db.commit()
    return [MedicalRecordOut.model_validate(r) for r in records]


@router.get("/patient/{patient_id}", response_model=list[MedicalRecordOut])
def records_for_patient(patient_id: str, request: Request, db: DbSession, user: CurrentUser) -> list[MedicalRecordOut]:
    get_patient_profile_or_404(db, patient_id)

    if user.role == Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins must use /medical-records/meta for non-clinical metadata",
        )
    if user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        if patient.id != patient_id:
            write_audit(
                db,
                action="authz.denied",
                actor=user,
                resource_type="medical_record",
                resource_id=patient_id,
                detail="Patient attempted cross-patient record access",
                correlation_id=_corr(request),
                success=False,
            )
            db.commit()
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
    write_audit(
        db,
        action="records.list",
        actor=user,
        resource_type="patient",
        resource_id=patient_id,
        correlation_id=_corr(request),
    )
    db.commit()
    return [MedicalRecordOut.model_validate(r) for r in records]


@router.get("/{record_id}", response_model=MedicalRecordOut)
def get_record(record_id: str, request: Request, db: DbSession, user: CurrentUser) -> MedicalRecordOut:
    record = db.get(MedicalRecord, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if user.role == Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins must use /medical-records/meta for non-clinical metadata",
        )
    if user.role == Role.PATIENT.value:
        patient = get_patient_profile_for_user(db, user)
        if record.patient_id != patient.id:
            write_audit(
                db,
                action="authz.denied",
                actor=user,
                resource_type="medical_record",
                resource_id=record_id,
                correlation_id=_corr(request),
                success=False,
            )
            db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif user.role == Role.DOCTOR.value:
        assert_doctor_authorized_for_patient(db, user, record.patient_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    write_audit(
        db,
        action="records.read",
        actor=user,
        resource_type="medical_record",
        resource_id=record_id,
        correlation_id=_corr(request),
    )
    db.commit()
    return MedicalRecordOut.model_validate(record)


@router.post("", response_model=MedicalRecordOut, status_code=status.HTTP_201_CREATED)
def add_record(
    payload: MedicalRecordCreate,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> MedicalRecordOut:
    doctor = assert_doctor_authorized_for_patient(db, user, payload.patient_id)
    record = MedicalRecord(
        patient_id=payload.patient_id,
        created_by_doctor_id=doctor.id,
        appointment_id=payload.appointment_id,
        title=payload.title,
        diagnosis=payload.diagnosis,
        prescription_notes=payload.prescription_notes,
        treatment=payload.treatment,
        notes=payload.notes,
    )
    db.add(record)
    db.flush()

    patient = db.get(PatientProfile, payload.patient_id)
    if patient:
        db.add(
            Notification(
                user_id=patient.user_id,
                title="New consultation notes",
                message="A doctor added new synthetic consultation notes to your records.",
                category="records",
            )
        )

    write_audit(
        db,
        action="records.create",
        actor=user,
        resource_type="medical_record",
        resource_id=record.id,
        correlation_id=_corr(request),
        detail="Synthetic consultation notes created",
    )
    db.commit()
    db.refresh(record)
    return MedicalRecordOut.model_validate(record)


@router.patch("/{record_id}", response_model=MedicalRecordOut)
def update_record(
    record_id: str,
    payload: MedicalRecordUpdate,
    request: Request,
    db: DbSession,
    user: User = Depends(require_roles(Role.DOCTOR)),
) -> MedicalRecordOut:
    record = db.get(MedicalRecord, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    doctor = assert_doctor_authorized_for_patient(db, user, record.patient_id)
    if record.created_by_doctor_id and record.created_by_doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the authoring doctor may update this record")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(record, key, value)

    write_audit(
        db,
        action="records.update",
        actor=user,
        resource_type="medical_record",
        resource_id=record_id,
        correlation_id=_corr(request),
        detail="Updated fields: " + ", ".join(data.keys()),
    )
    db.commit()
    db.refresh(record)
    return MedicalRecordOut.model_validate(record)
