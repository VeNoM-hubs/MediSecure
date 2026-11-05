# MediSecure API

Base path: `/api/v1`  
Interactive docs: `/docs` (OpenAPI)

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/change-password`
- `GET /auth/me`

## Patients / Doctors / Appointments / Records

- `GET|PUT /patients/me`
- `GET /patients/{patient_id}`
- `GET /doctors`
- `GET /doctors/{doctor_id}`
- `GET /doctors/{doctor_id}/availability`
- `POST|GET /appointments`
- `GET|PATCH|DELETE /appointments/{id}` (+ `/status`, `/cancel`)
- `GET|POST /medical-records`
- `GET /medical-records/{record_id}`

## Admin / Health

- `GET /admin/dashboard`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}/status`
- `GET /admin/audit-logs`
- `GET /health`
- `GET /ready`
