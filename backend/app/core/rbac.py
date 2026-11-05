from enum import StrEnum


class Role(StrEnum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


# Capability matrix for documentation / future policy engines (OPA, K8s RBAC mirrors)
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.PATIENT: {
        "profile:read_self",
        "profile:update_self",
        "doctors:list",
        "appointments:create_self",
        "appointments:read_self",
        "appointments:cancel_self",
        "records:read_self",
        "notifications:read_self",
        "password:change_self",
    },
    Role.DOCTOR: {
        "dashboard:doctor",
        "appointments:read_assigned",
        "appointments:update_assigned",
        "patients:read_authorized",
        "records:read_authorized",
        "records:add_notes",
        "schedule:read_self",
        "notifications:read_self",
    },
    Role.ADMIN: {
        "stats:read",
        "doctors:manage",
        "patients:manage",
        "appointments:manage",
        "accounts:activate",
        "audit:read",
        "specializations:manage",
    },
}
