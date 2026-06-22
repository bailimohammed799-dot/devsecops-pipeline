# 03 — Tooling

Every tool used in the pipeline, its version, configuration, and what it detects.

## Code Quality

### SonarQube Community Edition

- **Version:** Latest community Docker image (`sonarqube:community`)
- **Config:** `sonar-project.properties`
- **Detects:** Bugs, vulnerabilities, code smells, duplications, complexity
- **Quality Gate:** Fails on new bugs, vulnerabilities, or coverage below threshold
- **Access:** `http://localhost:9000` (admin/admin on first run)

## Unit Testing

### pytest

- **Version:** ≥ 7.0
- **Config:** `pytest.ini` or `pyproject.toml` in target app
- **Command:** `pytest tests/ -v --junitxml=junit.xml --cov=conduit`
- **Output:** JUnit XML (CI integration), terminal output

### coverage.py

- **Version:** ≥ 7.0 (via pytest-cov)
- **Config:** `.coveragerc` in target app
- **Threshold:** `MIN_COVERAGE` env var (default 60%)

## Static Security Analysis (SAST)

### Semgrep

- **Version:** Latest via pip (`pip install semgrep`)
- **Rulesets:** `p/owasp-top-ten`, `p/security-audit`, `p/python`
- **Output:** SARIF (GitHub Code Scanning compatible) + JSON
- **Detects:** SQL injection, XSS, path traversal, hardcoded secrets, unsafe deserialization

### Bandit

- **Version:** Latest via pip
- **Config:** Default rules (all severity levels)
- **Output:** JSON
- **Detects:** Python-specific: eval(), pickle, hardcoded passwords, assert in production, subprocess with shell=True

### Gitleaks

- **Version:** Latest (GitHub Action `gitleaks/gitleaks-action@v2` or CLI)
- **Config:** `.gitleaks.toml`
- **Detects:** Hardcoded secrets: AWS keys, GitHub tokens, private keys, database URLs, JWT tokens
- **Allowlist:** `.gitleaks.toml` for false positives

### pip-audit

- **Version:** Latest via pip
- **Detects:** Known CVEs in Python dependencies (uses PyPA advisory database)
- **Output:** JSON

## Container Security

### Trivy

- **Version:** Latest (GitHub Action `aquasecurity/trivy-action@master`)
- **Modes:** Filesystem scan (`trivy fs`) + Image scan (`trivy image`)
- **Severity filter:** HIGH, CRITICAL (configurable)
- **Detects:** OS package vulnerabilities, language-specific package CVEs, misconfigurations

### Docker

- **Version:** ≥ 24.0
- **Config:** `docker/Dockerfile` (multi-stage), `docker/docker-compose.yml`
- **Best practices:** Non-root user, distroless/slim base, HEALTHCHECK, labels

## Dynamic Security Testing (DAST)

### OWASP ZAP

- **Version:** `owasp/zap2docker-stable:latest`
- **Modes:** Baseline (passive) + Full (active spider + active scan)
- **Output:** HTML report + XML (JUnit-compatible) + JSON
- **Detects:** XSS, SQL injection, CSRF, path traversal, insecure cookies, missing headers

## Dependency Scanning

### OWASP Dependency-Check

- **Version:** `owasp/dependency-check:latest` Docker image
- **Run:** Nightly only (resource-intensive)
- **Detects:** Known CVEs in project dependencies (uses NVD database)
- **Output:** HTML report
