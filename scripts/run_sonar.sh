#!/bin/bash
# Stage 3 — SonarQube quality scan
set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir>}"
SONAR_HOST="${SONAR_HOST_URL:-http://localhost:9000}"
SONAR_TOKEN="${SONAR_TOKEN:-}"
PROJECT_DIR="/tmp/conduit-app"

echo "Waiting for SonarQube to be ready..."
MAX_RETRIES=30
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SONAR_HOST/api/system/status" 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
        SYSTEM_STATUS=$(curl -s "$SONAR_HOST/api/system/status" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
        if [ "$SYSTEM_STATUS" = "UP" ]; then
            echo "SonarQube is UP"
            break
        fi
    fi
    echo "  Waiting... ($RETRY/$MAX_RETRIES) status=$STATUS"
    sleep 10
    RETRY=$((RETRY + 1))
done

if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "ERROR: SonarQube did not become ready within timeout"
    exit 1
fi

echo "Running sonar-scanner..."
cd "$PROJECT_DIR"

sonar-scanner \
    -Dsonar.host.url="$SONAR_HOST" \
    -Dsonar.login="$SONAR_TOKEN" \
    -Dsonar.projectKey=conduit \
    -Dsonar.projectName="Conduit - DevSecOps Pipeline" \
    -Dsonar.sources=conduit \
    -Dsonar.tests=tests \
    -Dsonar.python.coverage.reportPaths="$OUTPUT_DIR/../04-tests/coverage.xml" \
    -Dsonar.python.xunit.reportPath="$OUTPUT_DIR/../04-tests/junit.xml" \
    2>&1 | tee "$OUTPUT_DIR/sonar-scanner.log"

# Fetch Quality Gate status
echo "Fetching Quality Gate status..."
PROJECT_STATUS=$(curl -s -u "$SONAR_TOKEN:" "$SONAR_HOST/api/qualitygates/project_status?projectKey=conduit")
echo "$PROJECT_STATUS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
status = data.get('projectStatus', {}).get('status', 'UNKNOWN')
print(f'Quality Gate: {status}')
" | tee "$OUTPUT_DIR/quality-gate.txt"

# Generate markdown report
python3 -c "
import json, sys, subprocess

# Fetch metrics
import urllib.request, base64
url = '$SONAR_HOST/api/measures/component?component=conduit&metricKeys=bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density,ncloc'
req = urllib.request.Request(url)
auth = base64.b64encode(b'$SONAR_TOKEN:').decode()
req.add_header('Authorization', f'Basic {auth}')
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    measures = {m['metric']: m['value'] for m in data.get('component', {}).get('measures', [])}
except Exception as e:
    measures = {'error': str(e)}

report = f'''# SonarQube Analysis Report

| Metric | Value |
|--------|-------|
| Bugs | {measures.get('bugs', 'N/A')} |
| Vulnerabilities | {measures.get('vulnerabilities', 'N/A')} |
| Code Smells | {measures.get('code_smells', 'N/A')} |
| Coverage | {measures.get('coverage', 'N/A')}% |
| Duplications | {measures.get('duplicated_lines_density', 'N/A')}% |
| Lines of Code | {measures.get('ncloc', 'N/A')} |

Dashboard: $SONAR_HOST/dashboard?id=conduit
'''
with open('$OUTPUT_DIR/sonar-report.md', 'w') as f:
    f.write(report)
print(report)
" 2>/dev/null || echo "Could not fetch detailed metrics (non-fatal)"

echo "Stage 3 complete."
