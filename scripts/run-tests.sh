#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"

echo "==> Backend tests"
cd "$ROOT/backend"
if [ -x .venv/bin/python ]; then
  .venv/bin/python -m pytest -q
elif [ -x .venv/Scripts/python.exe ]; then
  .venv/Scripts/python.exe -m pytest -q
else
  python -m pytest -q
fi

echo "==> Frontend tests"
cd "$ROOT/frontend"
npm test
