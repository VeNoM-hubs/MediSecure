from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.rbac import Role
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.medical_record import MedicalRecord
    from app.models.notification import Notification
    from app.models.refresh_token import RefreshToken
    from app.models.specialization import Specialization


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    patient_profile: Mapped["PatientProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    doctor_profile: Mapped["DoctorProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def has_role(self, role: Role) -> bool:
        return self.role == role.value


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    blood_type: Mapped[str | None] = mapped_column(String(8), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)

    user: Mapped[User] = relationship(back_populates="patient_profile")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
    medical_records: Mapped[list["MedicalRecord"]] = relationship(back_populates="patient")


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    specialization_id: Mapped[str | None] = mapped_column(
        ForeignKey("specializations.id", ondelete="SET NULL"), nullable=True
    )
    license_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    qualifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="doctor_profile")
    specialization: Mapped["Specialization | None"] = relationship(back_populates="doctors")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
