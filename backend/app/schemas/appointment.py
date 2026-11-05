from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    doctor_id: str
    scheduled_at: datetime
    reason: str | None = Field(default=None, max_length=2000)
    slot_id: str | None = None


class AppointmentStatusUpdate(BaseModel):
    status: str = Field(pattern="^(scheduled|pending|confirmed|completed|cancelled|rejected|no_show)$")
    consultation_notes: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    scheduled_at: datetime
    status: str
    reason: str | None = None
    consultation_notes: str | None = None
    patient_name: str | None = None
    doctor_name: str | None = None
    created_at: datetime


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    starts_at: datetime
    ends_at: datetime
    is_booked: bool
