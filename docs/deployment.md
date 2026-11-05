# Deployment

## Local Compose

```bash
cp .env.example .env
docker compose up --build
```

## Kubernetes (K3s-compatible)

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
