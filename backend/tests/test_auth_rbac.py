from datetime import UTC, datetime, timedelta

from tests.conftest import auth_header


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_login_and_me(client):
    headers = auth_header(client, "patient@example.com")
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "patient"
    assert "password_hash" not in me.json()


def test_patient_cannot_read_other_patient(client, db_session):
    from app.models.user import PatientProfile, User
    from sqlalchemy import select

    other = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "other@example.com")
    )
    headers = auth_header(client, "patient@example.com")
    res = client.get(f"/api/v1/patients/{other.id}", headers=headers)
    assert res.status_code == 403


def test_doctor_cannot_read_patient_without_appointment(client, db_session):
    from app.models.user import PatientProfile
    from sqlalchemy import select

    patient = db_session.scalar(select(PatientProfile))
    headers = auth_header(client, "doctor@example.com")
    res = client.get(f"/api/v1/patients/{patient.id}", headers=headers)
    assert res.status_code == 403


def test_doctor_can_read_patient_with_appointment(client, db_session):
    from app.models.appointment import Appointment
    from app.models.user import DoctorProfile, PatientProfile, User
    from sqlalchemy import select

    doctor = db_session.scalar(select(DoctorProfile))
    patient = db_session.scalar(
        select(PatientProfile)
        .join(User, PatientProfile.user_id == User.id)
        .where(User.email == "patient@example.com")
    )
    db_session.add(
        Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_at=datetime.now(UTC) + timedelta(days=1),
            status="scheduled",
            reason="synthetic visit",
        )
    )
    db_session.commit()

    headers = auth_header(client, "doctor@example.com")
    res = client.get(f"/api/v1/patients/{patient.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["email"] == "patient@example.com"


def test_admin_stats_no_password_leak(client):
    headers = auth_header(client, "admin@example.com")
    res = client.get("/api/v1/admin/stats", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "total_patients" in body

    patients = client.get("/api/v1/admin/patients", headers=headers)
    assert patients.status_code == 200
    for row in patients.json():
        assert "password" not in row
        assert "password_hash" not in row


def test_book_and_cancel_appointment(client, db_session):
    from app.models.user import DoctorProfile
    from sqlalchemy import select

    doctor = db_session.scalar(select(DoctorProfile))
    headers = auth_header(client, "patient@example.com")
    when = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    booked = client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"doctor_id": doctor.id, "scheduled_at": when, "reason": "Checkup"},
    )
    assert booked.status_code == 201, booked.text
    appt_id = booked.json()["id"]

    cancelled = client.post(f"/api/v1/appointments/{appt_id}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
