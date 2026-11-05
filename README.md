# MediSecure

Academic **DevSecOps** healthcare management platform with strict RBAC, refresh-token auth, appointment slots, audit logging, and CI/CD hooks for Jenkins, Docker, Trivy, SonarQube, and K3s.

> Synthetic / fictional clinical data only. Not for real patient care.

## Architecture

See [docs/architecture.md](docs/architecture.md) for Mermaid diagrams (system, data flow, pipeline).

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, React Router, Axios, React Hook Form, Zod |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, JWT, Argon2 |
| Testing | Pytest, Vitest, React Testing Library |
| Delivery | Docker Compose, `jenkins/Jenkinsfile`, K8s manifests, Trivy scripts |

## Features (complete application)

- **Auth:** patient registration; patient/doctor/admin login; Argon2; JWT + refresh rotation; logout; lockout/rate limits
- **RBAC/IDOR:** backend-enforced roles and ownership checks
- **Patient:** doctor directory, booking, appointments, records, notifications, profile
- **Doctor:** appointment accept/reject/complete, availability slots, authorized patient records, consultation notes
- **Admin:** live stats dashboard, appointment management, users/doctors, specializations, audit logs (clinical content redacted via `/meta`)
- **UX (Phase 4):** role dashboards, breadcrumbs, skeletons/spinners, confirm dialogs, toasts, responsive shell, accessible labels/focus
- **Containers (Phase 5):** production Dockerfiles, Compose demo on `:8080`, Nginx `/api/` proxy, non-root images
- **Ops stubs:** `/health`, `/ready`, K8s/Jenkins/Trivy prepared (later phases)

## Phase 2 — Authentication & RBAC

### Auth endpoints (`/api/v1`)

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/auth/register` | Patient self-registration |
| POST | `/auth/login` | Patient / Doctor / Admin |
| POST | `/auth/refresh` | Rotating refresh tokens |
| POST | `/auth/logout` | Revokes refresh token(s) |
| POST | `/auth/change-password` | Requires current password |
| GET | `/auth/me` | Public profile fields only (no password hash) |

### Roles

Backend-enforced roles: `patient`, `doctor`, `admin` (`app.core.rbac.Role`).  
Frontend protected routes are complementary only — every sensitive API checks ownership/role.

### Auth setup notes

1. Copy `.env.example` → `.env` and set a strong `JWT_SECRET_KEY` (never commit secrets).
2. Apply migrations (`alembic upgrade head`) so `users`, `refresh_tokens`, and lockout columns exist.
3. Seed demo users (`python -m app.seed`) or register a patient via `/register`.
4. Access tokens expire quickly (`ACCESS_TOKEN_EXPIRE_MINUTES`); the SPA refreshes via `/auth/refresh` and redirects to login with `?expired=1` when refresh fails.

### Phase 2 tests

```bash
cd backend
.\.venv\Scripts\python -m pytest tests/test_phase2_auth.py tests/test_security.py tests/test_auth_rbac.py -q

cd ../frontend
npm test
```

## Phase 3 — Healthcare core

### Appointments
- Slot-aware booking, overlap/double-book prevention, UTC timestamps
- Status transitions: pending → confirmed/rejected → completed
- Paginated list with `status`, `q`, `upcoming`, `doctor_id`, `patient_id` filters
- Doctor slot CRUD: `GET/POST /doctors/me/slots`, `DELETE /doctors/me/slots/{id}`

### Medical records
- Patient self-access; doctor access only with appointment relationship
- Create/update consultation notes (synthetic)
- Admin metadata-only: `GET /medical-records/meta` (no diagnosis/prescription fields)

### Notifications
- Booking / accept / reject / cancel / complete / new notes
- `GET /notifications`, `GET /notifications/unread-count`, `POST .../read`, `POST /notifications/read-all`

### Phase 3 tests

```bash
cd backend
.\.venv\Scripts\python -m pytest tests/test_phase3_core.py -q
```

## Phase 4 — Integration & UI polish

- Role-specific dashboards fed by live APIs (no fabricated stats)
- Shared UI primitives: breadcrumbs, skeletons, error retry, confirm dialogs, focus styles
- Responsive sidebar + mobile navigation drawer
- Appointment cancel confirmation; toast feedback preserved
- Admin dashboard metrics include pending/completed/cancelled appointment counts

```bash
cd frontend
npm test
npm run build
```

## Demo login

| Role | Email | Password |
| --- | --- | --- |
| Admin | `bhaskar@gmail.com` | `12345678` |
| Doctor | `dr.rivera@medisecure.demo` | `12345678` |
| Patient | `patient.one@medisecure.demo` | `12345678` |

## Local development

```bash
cp .env.example .env

# Backend
cd backend
py -3.13 -m venv .venv   # or Python 3.12
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm ci
npm run dev
```

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/health  
Ready: http://localhost:8000/ready

### Tests

```bash
make test
# or
./scripts/run-tests.sh
```

## Phase 5 — Docker & containerization

### Prerequisites

- Docker Engine + Docker Compose v2
- Copy env template: `cp .env.example .env` (set `JWT_SECRET_KEY` and `POSTGRES_PASSWORD`)

### Build & start (production-oriented demo)

```bash
# Build images
docker compose -f docker-compose.yml build
# or: ./scripts/docker-build.sh

# Start stack (frontend :8080; Postgres not published; API via Nginx /api/)
docker compose -f docker-compose.yml up --build -d
# Windows: .\scripts\docker-up.ps1
```

### Development Compose (debug ports)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

Publishes Postgres `:5432` and backend `:8000` for local tooling. Do not use as a production profile.

### Migrations, health, logs, stop

| Action | Command |
| --- | --- |
| Migrations (auto on start) | `./scripts/docker-migrate.sh` or `docker compose exec backend alembic upgrade head` |
| Health | `./scripts/docker-health.sh` or `docker compose ps` |
| Logs | `./scripts/docker-logs.sh` |
| Stop **without** deleting DB data | `docker compose -f docker-compose.yml down` / `.\scripts\docker-down.ps1` |
| Stop **and** delete DB volume | `docker compose down -v` (destructive) |

### Access URLs

| URL | Notes |
| --- | --- |
| http://localhost:8080 | Application UI |
| http://localhost:8080/api/v1/... | API through Nginx proxy |
| http://localhost:8000/docs | Backend OpenAPI (dev compose only) |
| http://localhost:8000/health | Backend health (dev compose / in-network) |

### Data persistence

Named volume `medisecure_postgres_data` stores PostgreSQL data. `docker compose down` keeps it; `down -v` removes it.

### Troubleshooting

```bash
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml logs backend --tail=100
docker compose -f docker-compose.yml logs frontend --tail=100
docker compose -f docker-compose.yml exec backend curl -fsS http://127.0.0.1:8000/health
curl http://localhost:8080/health
```

### Container security notes

- Pinned slim/alpine base images; multi-stage builds
- Backend and frontend run as non-root
- `.dockerignore` excludes `.env`, venvs, tests, and secrets
- Production image installs `requirements-prod.txt` only (no pytest)
- Postgres not published in the default Compose file
- No privileged containers

## DevSecOps

| Concern | Location |
| --- | --- |
| Jenkins pipeline | `jenkins/Jenkinsfile` |
| Trivy FS/image | `scripts/scan-*.sh` |
| SonarQube | `sonar-project.properties` |
| K8s | `k8s/{config,security,database,backend,frontend}` |
| Secrets guidance | `docs/deployment.md`, `docs/security.md` |

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment.md)
- [Threat model](docs/threat-model.md)

## Implemented vs future placeholders

**Implemented:** auth/RBAC, refresh tokens, lockout, rate limit, appointments/slots, records, notifications, audit, dashboards, Compose, K8s templates, Jenkinsfile, Trivy scripts, Sonar properties, security tests.

**Placeholders / later wiring:** live Jenkins credentials, Sonar server, image registry push, Prometheus/Grafana stack, Redis rate-limit backend, Vault/External Secrets operators.
