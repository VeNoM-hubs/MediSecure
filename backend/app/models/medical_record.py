from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import PatientProfile


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id", ondelete="CASCADE"), index=True)
    created_by_doctor_id: Mapped[str | None] = mapped_column(
        ForeignKey("doctor_profiles.id", ondelete="SET NULL"), nullable=True
    )
    appointment_id: Mapped[str | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescription_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    record_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    patient: Mapped[PatientProfile] = relationship(back_populates="medical_records")
