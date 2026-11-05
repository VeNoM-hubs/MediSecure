"""Phase 2 — authentication, refresh tokens, and RBAC/IDOR coverage."""

from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.config import get_settings
from tests.conftest import auth_header


def test_successful_registration_and_login(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.patient@example.com",
            "password": "SecurePass123!",
            "full_name": "New Patient",
            "phone": "+1-555-0101",
        },
    )
    assert register.status_code == 201, register.text
    body = register.json()
    assert body["role"] == "patient"
    assert "access_token" in body
    assert "refresh_token" in body
    assert "password" not in body
    assert "password_hash" not in body

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "new.patient@example.com", "password": "SecurePass123!"},
    )
    assert login.status_code == 200
    assert login.json()["user_id"] == body["user_id"]


def test_incorrect_password(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@example.com", "password": "DefinitelyWrong!"},
    )
    assert res.status_code == 401
    assert "password" not in res.text.lower() or "invalid" in res.json()["detail"].lower()


def test_duplicate_registration(client):
    payload = {
        "email": "dup.patient@example.com",
        "password": "SecurePass123!",
        "full_name": "Dup Patient",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_all_roles(client):
    for email, role in [
        ("patient@example.com", "patient"),
        ("doctor@example.com", "doctor"),
        ("admin@example.com", "admin"),
    ]:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass123!"})
        assert res.status_code == 200, res.text
        assert res.json()["role"] == role
        assert "password_hash" not in res.json()


def test_logout_revokes_refresh_token(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@example.com", "password": "TestPass123!"},
    )
    assert login.status_code == 200
    access = login.json()["access_token"]
    refresh = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access}"},
        json={"refresh_token": refresh},
    )
    assert logout.status_code == 200

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert reused.status_code == 401


def test_refresh_rotation_and_reuse_rejected(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@example.com", "password": "TestPass123!"},
    )
    refresh = login.json()["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != refresh
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401


def test_expired_and_invalid_tokens(client, db_session):
    from app.models.user import User
    from sqlalchemy import select

    user = db_session.scalar(select(User).where(User.email == "patient@example.com"))
    settings = get_settings()
    expired = jwt.encode(
        {"sub": user.id, "exp": datetime.now(UTC) - timedelta(minutes=1), "type": "access"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer junk.token.value"}).status_code == 401


def test_unauthorized_without_token(client):
    assert client.get("/api/v1/patients/me").status_code == 401
    assert client.get("/api/v1/admin/dashboard").status_code == 401


def test_patient_cannot_access_other_patient_profile(client, db_session):
    from app.models.user import PatientProfile, User
    from sqlalchemy import select

    other = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "other@example.com")
    )
    headers = auth_header(client, "patient@example.com")
    assert client.get(f"/api/v1/patients/{other.id}", headers=headers).status_code == 403


def test_patient_cannot_access_other_medical_records(client, db_session):
    from app.models.medical_record import MedicalRecord
    from app.models.user import PatientProfile, User
    from sqlalchemy import select

    other = db_session.scalar(
        select(PatientProfile).join(User, PatientProfile.user_id == User.id).where(User.email == "other@example.com")
    )
    record = MedicalRecord(
        patient_id=other.id,
        title="Other patient synthetic record",
        diagnosis="Fictional",
    )
    db_session.add(record)
    db_session.commit()

    headers = auth_header(client, "patient@example.com")
    assert client.get(f"/api/v1/medical-records/patient/{other.id}", headers=headers).status_code == 403
    assert client.get(f"/api/v1/medical-records/{record.id}", headers=headers).status_code == 403


def test_doctor_cannot_access_unauthorized_patient_records(client, db_session):
    from app.models.medical_record import MedicalRecord
    from app.models.user import PatientProfile, User
    from sqlalchemy import select

    patient = db_session.scalar(
        select(PatientProfile)
        .join(User, PatientProfile.user_id == User.id)
        .where(User.email == "patient@example.com")
    )
    record = MedicalRecord(
        patient_id=patient.id,
        title="Unauth doctor should not see",
        diagnosis="Fictional",
    )
    db_session.add(record)
    db_session.commit()

    headers = auth_header(client, "doctor@example.com")
    assert client.get(f"/api/v1/medical-records/patient/{patient.id}", headers=headers).status_code == 403
    assert client.get(f"/api/v1/patients/{patient.id}", headers=headers).status_code == 403


def test_admin_permissions(client):
    headers = auth_header(client, "admin@example.com")
    assert client.get("/api/v1/admin/dashboard", headers=headers).status_code == 200
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 200
    assert client.get("/api/v1/admin/audit-logs", headers=headers).status_code == 200

    users = client.get("/api/v1/admin/users", headers=headers).json()
    for row in users:
        assert "password" not in row
        assert "password_hash" not in row


def test_me_never_returns_password_hash(client):
    headers = auth_header(client, "admin@example.com")
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert set(me.json().keys()) >= {"id", "email", "full_name", "role", "is_active"}
    assert "password_hash" not in me.json()
