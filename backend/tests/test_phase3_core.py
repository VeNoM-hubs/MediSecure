"""Phase 3 — appointments, records, notifications, audit."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models.appointment import Appointment
from app.models.appointment_slot import AppointmentSlot
from app.models.audit import AuditLog
from app.models.medical_record import MedicalRecord
from app.models.notification import Notification
from app.models.user import DoctorProfile, PatientProfile, User
from tests.conftest import auth_header


def test_successful_booking_and_notifications(client, db_session):
    doctor = db_session.scalar(select(DoctorProfile))
    starts = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=2, hours=10)
    slot = AppointmentSlot(
        doctor_id=doctor.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=30),
        is_booked=False,
    )
    db_session.add(slot)
    db_session.commit()

    headers = auth_header(client, "patient@example.com")
    booked = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={
            "doctor_id": doctor.id,
            "slot_id": slot.id,
            "scheduled_at": starts.isoformat(),
            "reason": "Synthetic checkup",
        },
    )
    assert booked.status_code == 201, booked.text
    appt_id = booked.json()["id"]

    patient = db_session.scalar(select(User).where(User.email == "patient@example.com"))
    doctor_user = db_session.get(User, doctor.user_id)
    notes = db_session.scalars(select(Notification).where(Notification.user_id.in_([patient.id, doctor_user.id]))).all()
    assert any("booked" in n.title.lower() or "request" in n.title.lower() for n in notes)

    audits = db_session.scalars(select(AuditLog).where(AuditLog.action == "appointment.create")).all()
    assert any(a.resource_id == appt_id for a in audits)


def test_double_booking_and_overlap_prevention(client, db_session):
    doctor = db_session.scalar(select(DoctorProfile))
    patient = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "patient@example.com")
    )
    when = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=4, hours=9)
    db_session.add(
        Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_at=when,
            status="confirmed",
            reason="Existing",
        )
    )
    db_session.commit()

    headers = auth_header(client, "patient@example.com")
    conflict = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"doctor_id": doctor.id, "scheduled_at": when.isoformat(), "reason": "Conflict"},
    )
    assert conflict.status_code == 409

    near = when + timedelta(minutes=15)
    overlap = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"doctor_id": doctor.id, "scheduled_at": near.isoformat(), "reason": "Overlap"},
    )
    assert overlap.status_code == 409


def test_unauthorized_appointment_access(client, db_session):
    doctor = db_session.scalar(select(DoctorProfile))
    other = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "other@example.com")
    )
    appt = Appointment(
        patient_id=other.id,
        doctor_id=doctor.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=5),
        status="pending",
        reason="Other",
    )
    db_session.add(appt)
    db_session.commit()

    headers = auth_header(client, "patient@example.com")
    assert client.get(f"/api/v1/appointments/{appt.id}", headers=headers).status_code == 403


def test_invalid_transition_and_consultation_notes(client, db_session):
    doctor = db_session.scalar(select(DoctorProfile))
    patient = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "patient@example.com")
    )
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=6),
        status="completed",
        reason="Already done",
        consultation_notes="Prior notes",
    )
    db_session.add(appt)
    db_session.commit()

    headers = auth_header(client, "doctor@example.com")
    invalid = client.patch(
        f"/api/v1/appointments/{appt.id}/status",
        headers=headers,
        json={"status": "confirmed"},
    )
    assert invalid.status_code == 400

    pending = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=6, hours=2),
        status="pending",
        reason="Notes flow",
    )
    db_session.add(pending)
    db_session.commit()
    ok = client.patch(
        f"/api/v1/appointments/{pending.id}/status",
        headers=headers,
        json={"status": "confirmed", "consultation_notes": "Synthetic note"},
    )
    assert ok.status_code == 200
    assert ok.json()["consultation_notes"] == "Synthetic note"


def test_record_isolation_and_doctor_create(client, db_session):
    doctor = db_session.scalar(select(DoctorProfile))
    patient = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "patient@example.com")
    )
    other = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "other@example.com")
    )
    db_session.add(
        Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_at=datetime.now(UTC) + timedelta(days=7),
            status="confirmed",
            reason="Authorize",
        )
    )
    db_session.commit()

    doctor_headers = auth_header(client, "doctor@example.com")
    created = client.post(
        "/api/v1/medical-records",
        headers=doctor_headers,
        json={
            "patient_id": patient.id,
            "title": "Synthetic consult",
            "diagnosis": "Fictional",
            "treatment": "Rest",
        },
    )
    assert created.status_code == 201, created.text

    # Unauthorized patient cannot create for other without relationship
    denied = client.post(
        "/api/v1/medical-records",
        headers=doctor_headers,
        json={"patient_id": other.id, "title": "Should fail"},
    )
    assert denied.status_code == 403

    patient_headers = auth_header(client, "patient@example.com")
    assert client.get(f"/api/v1/medical-records/patient/{other.id}", headers=patient_headers).status_code == 403

    # Notification for new notes
    notes = db_session.scalars(
        select(Notification).where(Notification.user_id == patient.user_id, Notification.category == "records")
    ).all()
    assert len(notes) >= 1


def test_notification_ownership_and_read(client, db_session):
    patient = db_session.scalar(select(User).where(User.email == "patient@example.com"))
    other = db_session.scalar(select(User).where(User.email == "other@example.com"))
    note = Notification(user_id=other.id, title="Secret", message="Not yours", category="system")
    own = Notification(user_id=patient.id, title="Mine", message="Hello", category="system", is_read=False)
    db_session.add_all([note, own])
    db_session.commit()

    headers = auth_header(client, "patient@example.com")
    listed = client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200
    assert all(n["title"] != "Secret" for n in listed.json())

    count = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.status_code == 200
    assert count.json()["unread_count"] >= 1

    marked = client.post(f"/api/v1/notifications/{own.id}/read", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True

    # Cannot mark another user's notification
    assert client.post(f"/api/v1/notifications/{note.id}/read", headers=headers).status_code == 404


def test_admin_record_meta_not_clinical(client, db_session):
    patient = db_session.scalar(select(PatientProfile))
    db_session.add(
        MedicalRecord(
            patient_id=patient.id,
            title="Clinical",
            diagnosis="Should not appear in meta for unrestricted admin clinical access path",
            prescription_notes="secret-synth",
        )
    )
    db_session.commit()
    headers = auth_header(client, "admin@example.com")
    meta = client.get("/api/v1/medical-records/meta", headers=headers)
    assert meta.status_code == 200
    assert meta.json()
    assert "diagnosis" not in meta.json()[0]
    assert "prescription_notes" not in meta.json()[0]
    assert client.get("/api/v1/medical-records/mine", headers=headers).status_code == 403


def test_doctor_slot_management(client):
    headers = auth_header(client, "doctor@example.com")
    starts = (datetime.now(UTC) + timedelta(days=8)).replace(minute=0, second=0, microsecond=0)
    created = client.post(
        "/api/v1/doctors/me/slots",
        headers=headers,
        json={"starts_at": starts.isoformat()},
    )
    assert created.status_code == 201, created.text
    slot_id = created.json()["id"]
    listed = client.get("/api/v1/doctors/me/slots", headers=headers)
    assert any(s["id"] == slot_id for s in listed.json())
    deleted = client.delete(f"/api/v1/doctors/me/slots/{slot_id}", headers=headers)
    assert deleted.status_code == 204
