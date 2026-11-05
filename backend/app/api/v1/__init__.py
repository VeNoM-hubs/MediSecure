from fastapi import APIRouter

from app.api.v1 import admin, appointments, auth, doctors, medical_records, notifications, patients, specializations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(doctors.router, prefix="/doctors", tags=["doctors"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(medical_records.router, prefix="/medical-records", tags=["medical-records"])
# Backward-compatible alias
api_router.include_router(medical_records.router, prefix="/records", tags=["medical-records-alias"], include_in_schema=False)
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(specializations.router, prefix="/specializations", tags=["specializations"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
