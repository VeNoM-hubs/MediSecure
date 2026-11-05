# Deployment

## Local Compose (Phase 5)

Prerequisites: Docker Engine + Docker Compose v2, and a `.env` file.

```bash
cp .env.example .env
# Edit JWT_SECRET_KEY and POSTGRES_PASSWORD before any shared use

# Production-oriented demo (frontend :8080, Postgres not published)
docker compose -f docker-compose.yml up --build -d

# Development overrides (publish Postgres :5432 and API :8000)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Stop without deleting DB volume
docker compose -f docker-compose.yml down

# Destroy DB volume only when intentional
docker compose -f docker-compose.yml down -v
```

Helper scripts: `scripts/docker-*.sh` and `scripts/docker-up.ps1` / `docker-down.ps1`.

| URL | Purpose |
| --- | --- |
| http://localhost:8080 | SPA (Nginx) |
| http://localhost:8080/api/v1 | API via Nginx proxy |
| http://localhost:8000/docs | API docs (dev compose only) |

Migrations run automatically on backend container start (`alembic upgrade head`). Re-run with `scripts/docker-migrate.sh`.

## Kubernetes (K3s-compatible)

Phase 5 does not deploy to Kubernetes. Existing manifests remain under `k8s/` for a later phase.

1. Create namespace + config: `k8s/config/`
2. Apply secrets from a secure channel (never commit real values): `k8s/config/secret.example.yaml`
3. Apply security: `k8s/security/`
4. Apply database (optional): `k8s/database/`
5. Apply backend/frontend: `k8s/backend/`, `k8s/frontend/`

PostgreSQL Service is ClusterIP only.

## Jenkins

Use `jenkins/Jenkinsfile`. Credentials expected later:

- `registry-credentials`
- `kubeconfig-medisecure`
- SonarQube server binding named `SonarQube`

Parameters drive registry, severity thresholds, push, and deploy flags.

## Secrets

| Location | Purpose |
| --- | --- |
| `.env` (gitignored) | Local only |
| Jenkins Credentials | CI secrets |
| Kubernetes Secret | Runtime secrets |
