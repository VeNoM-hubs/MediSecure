#!/usr/bin/env sh
# Build and start the production-oriented Compose stack.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.example to .env and set secrets first." >&2
  exit 1
fi

docker compose -f docker-compose.yml up --build -d "$@"
echo "MediSecure started. UI: http://localhost:${FRONTEND_HOST_PORT:-8080}"
