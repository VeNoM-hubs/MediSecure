#!/usr/bin/env sh
# Stop containers without deleting the postgres_data volume.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose -f docker-compose.yml -f docker-compose.dev.yml down "$@"
echo "Containers stopped. Volume medisecure_postgres_data was preserved (no -v)."
