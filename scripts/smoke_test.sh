#!/bin/bash
# Stage 7 — Smoke test after deployment
set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir>}"
APP_URL="${APP_URL:-http://localhost:8080}"
MAX_RETRIES=30
RETRY=0

echo "Smoke testing $APP_URL..."

# Wait for health endpoint
echo "Waiting for app health check..."
while [ $RETRY -lt $MAX_RETRIES ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/api/healthz" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        echo "App is responding (HTTP $HTTP_CODE)"
        break
    fi
    echo "  Waiting... ($RETRY/$MAX_RETRIES) HTTP=$HTTP_CODE"
    sleep 5
    RETRY=$((RETRY + 1))
done

if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "ERROR: App did not become healthy within timeout"
    exit 1
fi

echo "=== Smoke Test Results ==="
RESULTS=()
PASS=0
FAIL=0

# Test 1: Root endpoint
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/api/" 2>/dev/null)
echo "  GET /api/ -> $HTTP"
RESULTS+=("GET /api/|$HTTP")

# Test 2: Health endpoint  
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/api/healthz" 2>/dev/null)
echo "  GET /api/healthz -> $HTTP"
RESULTS+=("GET /api/healthz|$HTTP")

# Test 3: Articles (public)
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL/api/articles" 2>/dev/null)
echo "  GET /api/articles -> $HTTP"
RESULTS+=("GET /api/articles|$HTTP")

# Test 4: Login endpoint exists
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/api/users/login" \
    -H "Content-Type: application/json" \
    -d '{"user":{"email":"test@test.com","password":"test"}}' 2>/dev/null)
echo "  POST /api/users/login -> $HTTP"
RESULTS+=("POST /api/users/login|$HTTP")

# Test 5: Registration endpoint
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$APP_URL/api/users" \
    -H "Content-Type: application/json" \
    -d '{"user":{"username":"smoketest","email":"smoke@test.com","password":"Test1234!"}}' 2>/dev/null)
echo "  POST /api/users -> $HTTP"
RESULTS+=("POST /api/users|$HTTP")

# Generate report
{
    echo "# Smoke Test Report"
    echo ""
    echo "| Endpoint | HTTP Status |"
    echo "|----------|-------------|"
    for r in "${RESULTS[@]}"; do
        IFS='|' read -r endpoint status <<< "$r"
        echo "| $endpoint | $status |"
    done
    echo ""
    echo "App URL: $APP_URL"
    echo "Timestamp: $(date -Iseconds)"
} > "$OUTPUT_DIR/smoke-test.md"

echo "Stage 7 complete. Smoke test report at $OUTPUT_DIR/smoke-test.md"
