# 02 — Pipeline Stages

Detailed breakdown of each stage in the DevSecOps pipeline.

---

## Stage 1: Source Code Retrieval & Integrity

**Purpose:** Clone the target application at a pinned commit and verify integrity.

**Commands:**
```bash
git clone https://github.com/${TARGET_REPO}.git /tmp/conduit-app
cd /tmp/conduit-app && git checkout ${TARGET_COMMIT}
git log --show-signature -1
gitleaks detect --source . -v --no-git
```

**Expected runtime:** ~30 seconds  
**Expected outputs:** `reports/<run>/01-source/clone-manifest.json`  
**Failure modes:** SHA mismatch, Gitleaks finding hardcoded secrets in history  
**Debug:** Check `TARGET_COMMIT` env var is set correctly. Verify network access to GitHub.

---

## Stage 2: Build

**Purpose:** Install dependencies and verify the application compiles/imports correctly.

**Commands:**
```bash
pip install -r requirements.txt
python -c "import conduit; print('Build OK')"
```

**Expected runtime:** ~2 minutes (first run, with pip downloads)  
**Expected outputs:** `reports/<run>/02-build/build.log`, `build-status.json`  
**Failure modes:** Missing system dependencies (psycopg2 needs libpq-dev), incompatible Python version

---

## Stage 3: SonarQube Quality Scan

**Purpose:** Static code quality analysis — bugs, code smells, duplications, maintainability.

**Commands:**
```bash
docker compose up -d sonarqube
# Wait for /api/system/status to return UP
sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.login=$SONAR_TOKEN
```

**Expected runtime:** ~3 minutes (including SonarQube startup)  
**Expected outputs:** `reports/<run>/03-sonar/sonar-report.md`, Dashboard at http://localhost:9000  
**Failure modes:** SonarQube fails to start (check Docker memory ≥ 2GB), Quality Gate fails

---

## Stage 4: Unit Tests & Coverage

**Purpose:** Run the application's test suite with coverage measurement.

**Commands:**
```bash
pytest tests/ -v --junitxml=junit.xml --cov=conduit --cov-report=xml:coverage.xml
```

**Expected runtime:** ~1 minute  
**Expected outputs:** `reports/<run>/04-tests/junit.xml`, `coverage.xml`, `tests-summary.md`  
**Failure modes:** Test failures, coverage below `MIN_COVERAGE` (default 60%)

---

## Stage 5: SAST (Static Application Security Testing)

**Purpose:** Find vulnerabilities in source code without executing it.

**Tools:**
| Tool | What it detects | Command |
|------|-----------------|---------|
| Semgrep | OWASP Top 10, security patterns | `semgrep scan --config p/owasp-top-ten --config p/python` |
| Bandit | Python-specific security issues | `bandit -r conduit/ -f json` |
| Gitleaks | Hardcoded secrets in git history | `gitleaks detect --source . -v` |
| pip-audit | Known vulnerabilities in dependencies | `pip-audit -r requirements.txt` |

**Expected runtime:** ~2 minutes  
**Expected outputs:** `reports/<run>/05-sast/semgrep.sarif`, `bandit.json`, `gitleaks.json`, `pip-audit.json`, `sast-summary.md`

---

## Stage 6: Image/Artifact Build

**Purpose:** Build a multi-stage Docker image, scan it, and push to local registry.

**Commands:**
```bash
docker build -t localhost:5000/conduit:latest -f docker/Dockerfile .
trivy fs --severity HIGH,CRITICAL /tmp/conduit-app
trivy image --severity HIGH,CRITICAL localhost:5000/conduit:latest
docker push localhost:5000/conduit:latest
```

**Expected runtime:** ~3 minutes  
**Expected outputs:** `reports/<run>/06-image/image-metadata.json`, `trivy-fs.json`, `trivy-image.json`

---

## Stage 7: Deploy to Test Environment

**Purpose:** Deploy the app + database via docker compose and verify it's reachable.

**Commands:**
```bash
docker compose -f docker/docker-compose.yml up -d
# Wait for http://localhost:8080/api/ to respond
curl -s http://localhost:8080/api/
```

**Expected runtime:** ~1 minute  
**Expected outputs:** `reports/<run>/07-deploy/deploy.log`, `smoke-test.md`

---

## Stage 8: Dynamic Security Testing (DAST)

**Purpose:** Test the running application for security vulnerabilities.

**Two modes:**
1. **Baseline (every PR):** Passive ZAP scan + all 12 custom scenarios
2. **Active (nightly):** Full active ZAP scan (spider, ajax spider, active rules)

**Custom scenarios:**
| # | Scenario | Test |
|---|----------|------|
| 1 | SQL Injection | OR 1=1, time-based payloads on all inputs |
| 2 | MITM | TLS config, HSTS, security headers |
| 3 | Broken Authentication | Weak passwords, default creds, rate limiting |
| 4 | Session Hijacking | Cookie flags, JWT expiry, fixation |
| 5 | Replay Attack | Request replay, idempotency, JWT jti |
| 6 | Privilege Escalation | Admin endpoint access, parameter tampering |
| 7 | API Abuse | Unauthenticated access, malformed payloads |
| 8 | DoS | Large payloads, slowloris, concurrency |
| 9 | Credential Stuffing | Leaked creds list, rate limit check |
| 10 | Security Misconfiguration | Headers, error pages, admin consoles |
| 11 | Sensitive Data Exposure | PII patterns, password hashing |
| 12 | Sender Spoofing | Email header injection (N/A for this app) |

---

## Stage 9: Report Generation

**Purpose:** Aggregate all findings into a single human-readable summary.

**Commands:**
```bash
python3 scripts/aggregate_reports.py reports/<run>/ <run-id>
```

**Expected runtime:** ~5 seconds  
**Expected outputs:** `reports/<run>/SUMMARY.md`
