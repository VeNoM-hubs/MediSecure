#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
OUT_DIR="${ROOT}/reports"
mkdir -p "$OUT_DIR"
SEVERITY="${TRIVY_SEVERITY:-HIGH,CRITICAL}"
IGNOREFILE="${TRIVY_IGNOREFILE:-/dev/null}"

# Explicit config/ignorefile avoids accidental loading from unrelated CWD.
trivy fs \
  --config "" \
  --ignorefile "$IGNOREFILE" \
  --severity "$SEVERITY" \
  --format json \
  --output "$OUT_DIR/trivy-fs.json" \
  "$ROOT"

trivy fs \
  --config "" \
  --ignorefile "$IGNOREFILE" \
  --severity "$SEVERITY" \
  --format table \
  --output "$OUT_DIR/trivy-fs.txt" \
  "$ROOT"

echo "Filesystem scan complete: $OUT_DIR/trivy-fs.*"
