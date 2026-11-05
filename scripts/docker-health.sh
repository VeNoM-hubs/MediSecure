#!/usr/bin/env sh
# Show container status and hit health endpoints.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Compose ps"
docker compose -f docker-compose.yml ps

echo "==> Backend /health (inside network)"
docker compose -f docker-compose.yml exec -T backend curl -fsS http://127.0.0.1:8000/health || true

echo "==> Frontend /health (host)"
curl -fsS "http://127.0.0.1:${FRONTEND_HOST_PORT:-8080}/health" || true
echo

echo "==> Frontend /api/v1 via proxy (expects 401/404 JSON, not connection error)"
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:${FRONTEND_HOST_PORT:-8080}/api/v1/auth/me" || true
