from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import DoctorProfile


class Specialization(Base):
    __tablename__ = "specializations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    doctors: Mapped[list["DoctorProfile"]] = relationship(back_populates="specialization")
