"""refresh tokens, lockout, slots, audit correlation, doctor quals

Revision ID: 0002_security
Revises: 0001_initial
Create Date: 2026-03-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_security"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    op.add_column("doctor_profiles", sa.Column("qualifications", sa.Text(), nullable=True))
    op.add_column("doctor_profiles", sa.Column("availability_notes", sa.Text(), nullable=True))

    op.add_column(
        "medical_records",
        sa.Column("appointment_id", sa.String(length=36), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("medical_records", sa.Column("prescription_notes", sa.Text(), nullable=True))
    op.create_index("ix_medical_records_appointment_id", "medical_records", ["appointment_id"])

    op.add_column("audit_logs", sa.Column("correlation_id", sa.String(length=64), nullable=True))
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("replaced_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "appointment_slots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("doctor_id", sa.String(length=36), sa.ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_booked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("doctor_id", "starts_at", name="uq_doctor_slot_start"),
    )
    op.create_index("ix_appointment_slots_doctor_id", "appointment_slots", ["doctor_id"])
    op.create_index("ix_appointment_slots_starts_at", "appointment_slots", ["starts_at"])


def downgrade() -> None:
    op.drop_table("appointment_slots")
    op.drop_table("refresh_tokens")
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_column("audit_logs", "correlation_id")
    op.drop_index("ix_medical_records_appointment_id", table_name="medical_records")
    op.drop_column("medical_records", "prescription_notes")
    op.drop_column("medical_records", "appointment_id")
    op.drop_column("doctor_profiles", "availability_notes")
    op.drop_column("doctor_profiles", "qualifications")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
