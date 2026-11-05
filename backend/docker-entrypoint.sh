#!/bin/sh
set -eu

echo "MediSecure backend: waiting for database and applying migrations..."
alembic upgrade head

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  echo "MediSecure backend: seeding demo data (SEED_DEMO_DATA=true)..."
  python -m app.seed
fi

echo "MediSecure backend: starting uvicorn..."
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips='*' \
  --no-access-log
