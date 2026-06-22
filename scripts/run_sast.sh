#!/bin/bash
# Stage 5 — SAST: Semgrep + Bandit + Gitleaks + Dependency scan
set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir>}"
PROJECT_DIR="/tmp/conduit-app"
cd "$PROJECT_DIR"

mkdir -p "$OUTPUT_DIR"
FAIL=0

echo "=== SAST: Semgrep ==="
semgrep scan \
    --config p/owasp-top-ten \
    --config p/security-audit \
    --config p/python \
    --sarif \
    --output "$OUTPUT_DIR/semgrep.sarif" \
    --json-output "$OUTPUT_DIR/semgrep.json" \
    conduit/ tests/ 2>&1 | tee "$OUTPUT_DIR/semgrep.log" || FAIL=1

echo "=== SAST: Bandit ==="
bandit -r conduit/ -f json -o "$OUTPUT_DIR/bandit.json" 2>&1 | tee "$OUTPUT_DIR/bandit.log" || true
# Bandit exits non-zero on findings; that's expected
BANDIT_EXIT=$?
if [ $BANDIT_EXIT -ne 0 ] && [ $BANDIT_EXIT -ne 1 ]; then
    echo "WARNING: Bandit exited with code $BANDIT_EXIT (findings or error)"
fi

echo "=== Secret scanning: Gitleaks ==="
gitleaks detect --source . -v --report-format json --report-path "$OUTPUT_DIR/gitleaks.json" 2>&1 | tee "$OUTPUT_DIR/gitleaks.log" || true

echo "=== Dependency scan: pip-audit ==="
pip-audit --format json --output "$OUTPUT_DIR/pip-audit.json" 2>&1 | tee "$OUTPUT_DIR/pip-audit.log" || true

echo "=== Aggregating SAST findings ==="
python3 -c "
import json, os, glob

outdir = '$OUTPUT_DIR'
findings = {'semgrep': [], 'bandit': [], 'gitleaks': [], 'pip_audit': []}
severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0, 'CRITICAL': 0}

# Parse Semgrep
try:
    with open(os.path.join(outdir, 'semgrep.json')) as f:
        data = json.load(f)
    for r in data.get('results', []):
        sev = r.get('extra', {}).get('severity', 'INFO').upper()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        findings['semgrep'].append({
            'rule': r.get('check_id', ''),
            'severity': sev,
            'path': r.get('path', ''),
            'line': r.get('start', {}).get('line', 0),
            'message': r.get('extra', {}).get('message', '')[:200]
        })
except Exception as e:
    print(f'Note: Could not parse Semgrep results: {e}')

# Parse Bandit
try:
    with open(os.path.join(outdir, 'bandit.json')) as f:
        data = json.load(f)
    for r in data.get('results', []):
        sev = r.get('issue_severity', 'LOW').upper()
        conf = r.get('issue_confidence', 'LOW').upper()
        if conf == 'HIGH':
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            findings['bandit'].append({
                'rule': r.get('test_id', ''),
                'severity': sev,
                'path': r.get('filename', ''),
                'line': r.get('line_number', 0),
                'message': r.get('issue_text', '')[:200]
            })
except Exception as e:
    print(f'Note: Could not parse Bandit results: {e}')

# Parse Gitleaks
try:
    with open(os.path.join(outdir, 'gitleaks.json')) as f:
        data = json.load(f)
    for r in data if isinstance(data, list) else []:
        severity_counts['HIGH'] += 1
        findings['gitleaks'].append({
            'rule': r.get('Description', r.get('RuleID', '')),
            'severity': 'HIGH',
            'path': r.get('File', ''),
            'line': r.get('StartLine', 0),
            'message': f\"Secret of type {r.get('Description', 'unknown')} found\"
        })
except Exception as e:
    print(f'Note: Could not parse Gitleaks results: {e}')

# Parse pip-audit
try:
    with open(os.path.join(outdir, 'pip-audit.json')) as f:
        data = json.load(f)
    for vuln in data.get('vulnerabilities', data if isinstance(data, list) else []):
        if isinstance(vuln, dict):
            sev = 'HIGH'
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            findings['pip_audit'].append({
                'rule': vuln.get('id', vuln.get('name', '')),
                'severity': sev,
                'path': vuln.get('dependency', {}).get('name', '') if isinstance(vuln.get('dependency'), dict) else '',
                'line': 0,
                'message': vuln.get('description', '')[:200]
            })
except Exception as e:
    print(f'Note: Could not parse pip-audit results: {e}')

# Generate summary markdown
total = sum(severity_counts.values())
lines = [
    '# SAST Summary',
    '',
    f'Total findings: **{total}**',
    '',
    '## Severity Breakdown',
    '',
    '| Severity | Count |',
    '|----------|-------|',
]
for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
    lines.append(f'| {sev} | {severity_counts.get(sev, 0)} |')

lines += [
    '',
    '## Tools',
    f'- **Semgrep**: {len(findings[\"semgrep\"])} findings ([semgrep.sarif](semgrep.sarif))',
    f'- **Bandit**: {len(findings[\"bandit\"])} findings ([bandit.json](bandit.json))',
    f'- **Gitleaks**: {len(findings[\"gitleaks\"])} findings ([gitleaks.json](gitleaks.json))',
    f'- **pip-audit**: {len(findings[\"pip_audit\"])} findings ([pip-audit.json](pip-audit.json))',
]

with open(os.path.join(outdir, 'sast-summary.md'), 'w') as f:
    f.write('\n'.join(lines))
print('\n'.join(lines))
"

echo "=== SAST stage complete ==="
exit $FAIL
