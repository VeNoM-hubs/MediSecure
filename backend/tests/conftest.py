import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force deterministic test settings before app import
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from app.core.security import hash_password  # noqa: E402
from app.core.rbac import Role  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import DoctorProfile, PatientProfile, User  # noqa: E402
from app.models.specialization import Specialization  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()

    spec = Specialization(name="General Practice", description="Primary care")
    session.add(spec)
    session.flush()

    admin = User(
        email="admin@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Admin",
        role=Role.ADMIN.value,
    )
    doctor_user = User(
        email="doctor@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Doctor",
        role=Role.DOCTOR.value,
    )
    patient_user = User(
        email="patient@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Patient",
        role=Role.PATIENT.value,
    )
    other_patient = User(
        email="other@example.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Other Patient",
        role=Role.PATIENT.value,
    )
    session.add_all([admin, doctor_user, patient_user, other_patient])
    session.flush()

    doctor_profile = DoctorProfile(
        user_id=doctor_user.id,
        specialization_id=spec.id,
        license_number="MD-TEST",
        years_experience=5,
    )
    patient_profile = PatientProfile(user_id=patient_user.id, blood_type="O+")
    other_profile = PatientProfile(user_id=other_patient.id, blood_type="A+")
    session.add_all([doctor_profile, patient_profile, other_profile])
    session.commit()

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    yield session
    app.dependency_overrides.clear()
    session.close()


@pytest.fixture()
def client(db_session):
    with TestClient(app) as c:
        yield c


def auth_header(client: TestClient, email: str, password: str = "TestPass123!") -> dict[str, str]:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
