#!/usr/bin/env sh
# Run Alembic migrations inside the running backend container.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose -f docker-compose.yml exec -T backend alembic upgrade head
echo "Migrations applied."
