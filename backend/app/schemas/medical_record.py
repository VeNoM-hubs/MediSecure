from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicalRecordCreate(BaseModel):
    patient_id: str
    appointment_id: str | None = None
    title: str = Field(min_length=2, max_length=200)
    diagnosis: str | None = None
    prescription_notes: str | None = None
    treatment: str | None = None
    notes: str | None = None


class MedicalRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    created_by_doctor_id: str | None = None
    appointment_id: str | None = None
    title: str
    diagnosis: str | None = None
    prescription_notes: str | None = None
    treatment: str | None = None
    notes: str | None = None
    record_date: datetime
    created_at: datetime
