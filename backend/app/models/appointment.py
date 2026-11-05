from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import DoctorProfile, PatientProfile


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctor_profiles.id", ondelete="CASCADE"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    consultation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="appointments")
    doctor: Mapped[DoctorProfile] = relationship(back_populates="appointments")
