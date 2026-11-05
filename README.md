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

## Features

- Patient / doctor / admin role dashboards
- Argon2 + short-lived access tokens + rotating refresh tokens
- Login lockout + auth rate limiting
- Appointment slots, double-booking prevention, status transitions
- Synthetic medical records with ownership checks
- Notifications + immutable audit trail with correlation IDs
- `/health`, `/ready`, `/metrics` stubs

## Demo login

| Role | Email | Password |
| --- | --- | --- |
| Admin | `bhaskar@gmail.com` | `1234` |
| Doctor | `dr.rivera@medisecure.demo` | `1234` |
| Patient | `patient.one@medisecure.demo` | `1234` |

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

### Docker Compose

```bash
docker compose up --build
```

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
