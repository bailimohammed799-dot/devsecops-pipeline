#!/bin/bash
# Check security headers on the deployed app (used by Scenario 10)
set -euo pipefail

URL="${1:-http://localhost:8080}"

echo "=== Security Headers Check ==="
echo "Target: $URL"
echo ""

# Define headers to check
declare -A EXPECTED=(
    ["X-Content-Type-Options"]="nosniff"
    ["X-Frame-Options"]="DENY|SAMEORIGIN"
    ["X-XSS-Protection"]="1; mode=block"
    ["Strict-Transport-Security"]="present"
    ["Content-Security-Policy"]="present"
    ["Referrer-Policy"]="present"
    ["Permissions-Policy"]="present"
)

echo "| Header | Expected | Actual | Status |"
echo "|--------|----------|--------|--------|"

for header in "${!EXPECTED[@]}"; do
    expected="${EXPECTED[$header]}"
    actual=$(curl -sI "$URL" | grep -i "^$header:" | sed "s/^$header: //i" | tr -d '\r' || echo "MISSING")

    if [ "$actual" = "MISSING" ]; then
        if [ "$expected" = "present" ]; then
            echo "| $header | should be present | MISSING | ⚠️ MISSING |"
        else
            echo "| $header | $expected | MISSING | ❌ MISSING |"
        fi
    elif [ "$expected" = "present" ]; then
        echo "| $header | should be present | $actual | ✅ |"
    elif echo "$expected" | grep -q "|"; then
        # Multiple acceptable values
        if echo "$actual" | grep -qE "$expected"; then
            echo "| $header | $expected | $actual | ✅ |"
        else
            echo "| $header | $expected | $actual | ⚠️ |"
        fi
    elif [ "$actual" = "$expected" ]; then
        echo "| $header | $expected | $actual | ✅ |"
    else
        echo "| $header | $expected | $actual | ⚠️ |"
    fi
done

echo ""
echo "Run 'curl -I $URL' to inspect headers manually."
