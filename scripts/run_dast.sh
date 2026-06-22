#!/bin/bash
# Stage 8a — OWASP ZAP DAST
set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir>}"
APP_URL="${APP_URL:-http://localhost:8080}"
ZAP_IMAGE="owasp/zap2docker-stable:latest"

mkdir -p "$OUTPUT_DIR/zap"

echo "=== ZAP Baseline Scan ==="
docker run --rm --network host \
    -v "$(pwd)/$OUTPUT_DIR/zap:/zap/wrk" \
    "$ZAP_IMAGE" zap-baseline.py \
    -t "$APP_URL" \
    -r zap-baseline.html \
    -x zap-baseline.xml \
    -J zap-baseline.json \
    --auto \
    2>&1 | tee "$OUTPUT_DIR/zap/zap-baseline.log" || true

echo "ZAP baseline complete."

# Active scan (more thorough — takes longer)
if [ "${ZAP_ACTIVE:-false}" = "true" ]; then
    echo "=== ZAP Active Scan ==="
    docker run --rm --network host \
        -v "$(pwd)/$OUTPUT_DIR/zap:/zap/wrk" \
        "$ZAP_IMAGE" zap-full-scan.py \
        -t "$APP_URL" \
        -r zap-active.html \
        -x zap-active.xml \
        -J zap-active.json \
        2>&1 | tee "$OUTPUT_DIR/zap/zap-active.log" || true
    echo "ZAP active scan complete."
fi

echo "DAST stage complete."
