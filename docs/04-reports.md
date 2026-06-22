# 04 — Reports

How to read and interpret every report artifact produced by the pipeline.

## Report Directory Structure

```
reports/YYYYMMDD-HHMMSS/
├── SUMMARY.md                    # Executive summary (Stage 9)
├── 01-source/
│   └── clone-manifest.json       # Repo URL, SHA, license, file count
├── 02-build/
│   ├── build.log                 # pip install output
│   └── build-status.json         # {"status": "success"|"failure"}
├── 03-sonar/
│   ├── sonar-report.md           # Bugs, vulnerabilities, smells, coverage
│   ├── sonar-scanner.log         # Raw scanner output
│   └── quality-gate.txt          # "OK" or "ERROR"
├── 04-tests/
│   ├── junit.xml                 # Standard JUnit XML (CI-compatible)
│   ├── coverage.xml              # Cobertura XML coverage
│   ├── test-output.log           # Raw pytest output
│   └── tests-summary.md          # Human-readable test summary
├── 05-sast/
│   ├── semgrep.sarif             # SARIF format (GitHub Code Scanning)
│   ├── semgrep.json              # Raw Semgrep results
│   ├── bandit.json               # Bandit findings
│   ├── gitleaks.json             # Secret scan results
│   ├── pip-audit.json            # Dependency vulnerabilities
│   └── sast-summary.md           # Aggregated SAST summary
├── 06-image/
│   ├── image-metadata.json       # Image tag, labels, build time
│   ├── trivy-fs.json             # Filesystem vulnerability scan
│   ├── trivy-image.json          # Image vulnerability scan
│   ├── build.log                 # Docker build output
│   └── image-scan-summary.md     # Human-readable image scan summary
├── 07-deploy/
│   ├── deploy.log                # docker compose output
│   └── smoke-test.md             # Smoke test results table
├── 08-dast/
│   ├── zap/
│   │   ├── zap-baseline.html     # Interactive HTML report
│   │   ├── zap-baseline.xml      # XML (JUnit-compatible)
│   │   └── zap-baseline.json     # JSON
│   ├── scenarios/
│   │   ├── 01-SQL_Injection.md
│   │   ├── 02-MITM.md
│   │   ├── ...                    # One per scenario
│   │   └── 12-Sender_Spoofing.md
│   └── dast-summary.md
```

## Severity Mapping

| Tool | Critical | High | Medium | Low | Info |
|------|----------|------|--------|-----|------|
| Semgrep | ERROR | WARNING | — | — | INFO |
| Bandit | — | HIGH | MEDIUM | LOW | — |
| Gitleaks | — | HIGH | — | — | — |
| Trivy | CRITICAL | HIGH | MEDIUM | LOW | — |
| ZAP | High | Medium | Low | Informational | — |
| SonarQube | Blocker | Critical | Major | Minor | Info |

## How to Read SUMMARY.md

`SUMMARY.md` is the entry point. It contains:

1. **Run metadata:** ID, timestamp
2. **Stage-by-stage status:** Pass/fail for each stage
3. **SonarQube Quality Gate:** OK/ERROR + key metrics
4. **SAST findings count** by severity
5. **DAST scenario table:** 12 rows, one per scenario
6. **Top 5 risks:** Ranked by severity × exploitability × impact
7. **Artifact index:** Links to all raw reports

## How to Read SAST Reports

### Semgrep SARIF
- Open in VS Code with SARIF Viewer extension
- Uploaded to GitHub Code Scanning automatically
- Each finding includes: rule ID, file path, line number, message, severity

### Bandit JSON
- Parse with `python -m json.tool bandit.json`
- Key fields: `issue_severity`, `issue_confidence`, `test_id`, `filename`, `line_number`

### Gitleaks JSON
- Parse with `python -m json.tool gitleaks.json`
- Key fields: `Description`, `File`, `StartLine`, `Secret` (redacted)

### pip-audit JSON
- Key field: `vulnerabilities` array with `id`, `description`, `dependency`

## How to Read ZAP Reports

- **HTML:** Open in browser — interactive, with request/response evidence
- **XML:** Import into CI/CD dashboards (JUnit format)
- **JSON:** Machine-readable, key fields: `alerts` with `risk`, `url`, `evidence`
