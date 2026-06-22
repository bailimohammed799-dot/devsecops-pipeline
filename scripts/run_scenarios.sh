#!/bin/bash
# Stage 8b — Custom DAST scenarios (12 scenarios from cahier des charges)
set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir>}"
APP_URL="${APP_URL:-http://localhost:8080}"
SCENARIO_DIR="$OUTPUT_DIR/scenarios"
mkdir -p "$SCENARIO_DIR"

# Helper: run a scenario Python script
run_scenario() {
    local num=$1
    local name=$2
    echo "=== Scenario $num: $name ==="
    python3 "tests/security/scenario_${num}_$(echo "$name" | tr ' ' '_' | tr '[:upper:]' '[:lower:]').py" \
        --url "$APP_URL" --output "$SCENARIO_DIR/$num-$name.md" 2>&1 || echo "  (completed with findings)"
}

run_scenario 01 "SQL Injection"
run_scenario 02 "MITM"
run_scenario 03 "Broken Authentication"
run_scenario 04 "Session Hijacking"
run_scenario 05 "Replay Attack"
run_scenario 06 "Privilege Escalation"
run_scenario 07 "API Abuse"
run_scenario 08 "Denial of Service"
run_scenario 09 "Credential Stuffing"
run_scenario 10 "Security Misconfiguration"
run_scenario 11 "Sensitive Data Exposure"
run_scenario 12 "Sender Spoofing"

echo "All 12 scenarios complete."
