from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    phone: str | None = None
    created_at: datetime


class PatientProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    date_of_birth: str | None = None
    gender: str | None = None
    blood_type: str | None = None
    address: str | None = None
    emergency_contact: str | None = None


class PatientProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    is_active: bool
    date_of_birth: str | None = None
    gender: str | None = None
    blood_type: str | None = None
    address: str | None = None
    emergency_contact: str | None = None


class DoctorCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    phone: str | None = None
    specialization_id: str | None = None
    license_number: str | None = None
    qualifications: str | None = None
    bio: str | None = None
    years_experience: int = 0
    availability_notes: str | None = None


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    is_active: bool
    specialization_id: str | None = None
    specialization_name: str | None = None
    license_number: str | None = None
    qualifications: str | None = None
    bio: str | None = None
    years_experience: int = 0
    availability_notes: str | None = None


class AccountStatusUpdate(BaseModel):
    is_active: bool
