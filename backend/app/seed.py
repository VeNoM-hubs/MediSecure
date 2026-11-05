"""Idempotent demo data seeder — fictional users only."""

from sqlalchemy import select

from app.core.config import get_settings
from app.core.rbac import Role
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.appointment import Appointment
from app.models.appointment_slot import AppointmentSlot
from app.models.medical_record import MedicalRecord
from app.models.notification import Notification
from app.models.specialization import Specialization
from app.models.user import DoctorProfile, PatientProfile, User
from datetime import UTC, datetime, timedelta


DEMO_PASSWORD = "12345678"
DEMO_ADMIN_EMAIL = "bhaskar@gmail.com"


def seed() -> None:
    settings = get_settings()
    if not settings.seed_demo_data:
        print("SEED_DEMO_DATA disabled — skipping.")
        return

    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == DEMO_ADMIN_EMAIL)):
            # Keep demo accounts usable after DEMO_PASSWORD changes without wiping the DB.
            demo_emails = (
                DEMO_ADMIN_EMAIL,
                "dr.rivera@medisecure.demo",
                "dr.chen@medisecure.demo",
                "dr.okafor@medisecure.demo",
                "patient.one@medisecure.demo",
                "patient.two@medisecure.demo",
            )
            updated = 0
            for email in demo_emails:
                user = db.scalar(select(User).where(User.email == email))
                if user:
                    user.password_hash = hash_password(DEMO_PASSWORD)
                    updated += 1
            db.commit()
            print(f"Demo data already present — refreshed passwords for {updated} demo users.")
            return

        specs = [
            Specialization(name="General Practice", description="Primary care and wellness"),
            Specialization(name="Cardiology", description="Heart and vascular health"),
            Specialization(name="Dermatology", description="Skin conditions"),
            Specialization(name="Pediatrics", description="Child and adolescent care"),
        ]
        db.add_all(specs)
        db.flush()

        admin = User(
            email=DEMO_ADMIN_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            full_name="Bhaskar",
            role=Role.ADMIN.value,
            phone="+1-555-0100",
        )
        db.add(admin)

        doctors_data = [
            ("dr.rivera@medisecure.demo", "Dr. Maya Rivera", specs[0].id, "MD-1001", 12),
            ("dr.chen@medisecure.demo", "Dr. Wei Chen", specs[1].id, "MD-1002", 15),
            ("dr.okafor@medisecure.demo", "Dr. Amara Okafor", specs[2].id, "MD-1003", 8),
        ]
        doctor_profiles: list[DoctorProfile] = []
        for email, name, spec_id, license_no, years in doctors_data:
            u = User(
                email=email,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=name,
                role=Role.DOCTOR.value,
            )
            db.add(u)
            db.flush()
            dp = DoctorProfile(
                user_id=u.id,
                specialization_id=spec_id,
                license_number=license_no,
                qualifications="MBBS, MD (synthetic)",
                bio=f"Synthetic profile for {name}.",
                years_experience=years,
                availability_notes="Weekdays 09:00–17:00 UTC (synthetic)",
            )
            db.add(dp)
            db.flush()
            doctor_profiles.append(dp)

        patients_data = [
            ("patient.one@medisecure.demo", "Jordan Lee", "1990-04-12", "O+"),
            ("patient.two@medisecure.demo", "Sam Patel", "1985-11-03", "A-"),
        ]
        patient_profiles: list[PatientProfile] = []
        for email, name, dob, blood in patients_data:
            u = User(
                email=email,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name=name,
                role=Role.PATIENT.value,
            )
            db.add(u)
            db.flush()
            pp = PatientProfile(
                user_id=u.id,
                date_of_birth=dob,
                gender="unspecified",
                blood_type=blood,
                address="100 Synthetic Ave, Demo City",
                emergency_contact="Emergency Contact (555-0199)",
            )
            db.add(pp)
            db.flush()
            patient_profiles.append(pp)

        # Generate open slots for next few days
        for doctor in doctor_profiles:
            for day in range(1, 6):
                for hour in (9, 11, 14, 16):
                    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=day, hours=hour)
                    db.add(
                        AppointmentSlot(
                            doctor_id=doctor.id,
                            starts_at=start,
                            ends_at=start + timedelta(minutes=30),
                            is_booked=False,
                        )
                    )
        db.flush()

        appt = Appointment(
            patient_id=patient_profiles[0].id,
            doctor_id=doctor_profiles[0].id,
            scheduled_at=datetime.now(UTC) + timedelta(days=3),
            status="confirmed",
            reason="Annual wellness checkup (synthetic)",
        )
        db.add(appt)
        db.flush()

        db.add(
            MedicalRecord(
                patient_id=patient_profiles[0].id,
                created_by_doctor_id=doctor_profiles[0].id,
                appointment_id=appt.id,
                title="Baseline wellness summary",
                diagnosis="Healthy — synthetic baseline",
                prescription_notes="Continue hydration (fictional)",
                treatment="Lifestyle counseling",
                notes="Fictional record for academic demo only.",
            )
        )

        for u_email in ("patient.one@medisecure.demo", "dr.rivera@medisecure.demo", DEMO_ADMIN_EMAIL):
            u = db.scalar(select(User).where(User.email == u_email))
            if u:
                db.add(
                    Notification(
                        user_id=u.id,
                        title="Welcome to MediSecure",
                        message="This environment uses synthetic healthcare data only.",
                        category="system",
                    )
                )

        db.commit()
        print("Demo seed complete.")
        print(f"Primary demo login: {DEMO_ADMIN_EMAIL} / {DEMO_PASSWORD}")
        print("  dr.rivera@medisecure.demo / dr.chen@medisecure.demo / dr.okafor@medisecure.demo")
        print("  patient.one@medisecure.demo / patient.two@medisecure.demo")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
