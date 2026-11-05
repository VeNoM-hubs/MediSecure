#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
IMAGE="${1:?Usage: scan-image.sh <image-ref>}"
OUT_DIR="${ROOT}/reports"
mkdir -p "$OUT_DIR"
SEVERITY="${TRIVY_SEVERITY:-HIGH,CRITICAL}"
SAFE_NAME="$(echo "$IMAGE" | tr '/:' '__')"
IGNOREFILE="${TRIVY_IGNOREFILE:-/dev/null}"

trivy image \
  --config "" \
  --ignorefile "$IGNOREFILE" \
  --severity "$SEVERITY" \
  --format json \
  --output "$OUT_DIR/trivy-image-${SAFE_NAME}.json" \
  "$IMAGE"

trivy image \
  --config "" \
  --ignorefile "$IGNOREFILE" \
  --severity "$SEVERITY" \
  --format table \
  --output "$OUT_DIR/trivy-image-${SAFE_NAME}.txt" \
  "$IMAGE"

echo "Image scan complete for $IMAGE"
