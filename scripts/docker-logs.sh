#!/usr/bin/env sh
# Tail Compose application logs (default: follow all services).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose -f docker-compose.yml logs -f --tail=200 "$@"
