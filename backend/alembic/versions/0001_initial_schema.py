"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "specializations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "patient_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column("date_of_birth", sa.String(length=10), nullable=True),
        sa.Column("gender", sa.String(length=32), nullable=True),
        sa.Column("blood_type", sa.String(length=8), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("emergency_contact", sa.String(length=200), nullable=True),
    )

    op.create_table(
        "doctor_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True),
        sa.Column(
            "specialization_id",
            sa.String(length=36),
            sa.ForeignKey("specializations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("license_number", sa.String(length=64), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE")),
        sa.Column("doctor_id", sa.String(length=36), sa.ForeignKey("doctor_profiles.id", ondelete="CASCADE")),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="scheduled"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("consultation_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_scheduled_at", "appointments", ["scheduled_at"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    op.create_table(
        "medical_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patient_profiles.id", ondelete="CASCADE")),
        sa.Column(
            "created_by_doctor_id",
            sa.String(length=36),
            sa.ForeignKey("doctor_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("treatment", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("record_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_medical_records_patient_id", "medical_records", ["patient_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="general"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("actor_role", sa.String(length=32), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=36), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("medical_records")
    op.drop_table("appointments")
    op.drop_table("doctor_profiles")
    op.drop_table("patient_profiles")
    op.drop_table("specializations")
    op.drop_table("users")
