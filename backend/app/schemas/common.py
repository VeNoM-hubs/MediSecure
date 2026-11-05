from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SpecializationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class SpecializationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    message: str
    is_read: bool
    category: str
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_user_id: str | None = None
    actor_email: str | None = None
    actor_role: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    detail: str | None = None
    ip_address: str | None = None
    correlation_id: str | None = None
    success: bool
    created_at: datetime


class StatsOut(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    active_users: int
    recent_security_events: int
