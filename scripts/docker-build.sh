#!/usr/bin/env sh
# Build all Compose images without starting containers.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.example to .env first." >&2
  exit 1
fi

docker compose -f docker-compose.yml build "$@"
echo "Images built: medisecure-backend:local, medisecure-frontend:local"
