from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import get_settings
from tests.conftest import auth_header


def test_unauthenticated_rejected(client):
    res = client.get("/api/v1/patients/me")
    assert res.status_code == 401


def test_patient_cannot_access_admin(client):
    headers = auth_header(client, "patient@example.com")
    res = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res.status_code == 403


def test_expired_jwt_rejected(client, db_session):
    from app.models.user import User
    from sqlalchemy import select

    user = db_session.scalar(select(User).where(User.email == "patient@example.com"))
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": user.id,
            "exp": datetime.now(UTC) - timedelta(minutes=5),
            "type": "access",
            "role": "patient",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_invalid_jwt_rejected(client):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_sql_injection_style_login(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "attacker@example.com' OR 1=1 --", "password": "x"},
    )
    assert res.status_code in {401, 422}


def test_refresh_token_rotation(client):
    login = client.post("/api/v1/auth/login", json={"email": "patient@example.com", "password": "TestPass123!"})
    assert login.status_code == 200
    refresh = login.json()["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != refresh
    # Old refresh token should no longer work
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert reuse.status_code == 401


def test_invalid_appointment_transition(client, db_session):
    from app.models.appointment import Appointment
    from app.models.user import DoctorProfile, PatientProfile, User
    from sqlalchemy import select

    doctor = db_session.scalar(select(DoctorProfile))
    patient = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "patient@example.com")
    )
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        status="completed",
        reason="done",
    )
    db_session.add(appt)
    db_session.commit()

    headers = auth_header(client, "doctor@example.com")
    res = client.patch(
        f"/api/v1/appointments/{appt.id}/status",
        headers=headers,
        json={"status": "confirmed"},
    )
    assert res.status_code == 400


def test_login_lockout(client, db_session):
    from app.core.config import get_settings

    settings = get_settings()
    for _ in range(settings.login_max_failures):
        client.post("/api/v1/auth/login", json={"email": "patient@example.com", "password": "wrong-password"})
    locked = client.post("/api/v1/auth/login", json={"email": "patient@example.com", "password": "TestPass123!"})
    assert locked.status_code in {401, 423}
