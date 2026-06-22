# DevSecOps Pipeline — Quickstart

> **Stage d'été — Projet DevSecOps :** Pipeline complète avec Shift Left Security pour une application Flask.
> **Summer Internship Project:** Complete DevSecOps pipeline with Shift Left Security for a Flask web app.

[![CI](https://github.com/bailimohammed799-dot/devsecops-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/bailimohammed799-dot/devsecops-pipeline/actions/workflows/ci.yml)
[![CD](https://github.com/bailimohammed799-dot/devsecops-pipeline/actions/workflows/cd.yml/badge.svg)](https://github.com/bailimohammed799-dot/devsecops-pipeline/actions/workflows/cd.yml)
[![Nightly](https://github.com/bailimohammed799-dot/devsecops-pipeline/actions/workflows/nightly.yml/badge.svg)](https://github.com/bailimohammed799-dot/devsecops-pipeline/actions/workflows/nightly.yml)

## What This Is / Qu'est-ce que c'est

A complete, reproducible DevSecOps pipeline implementing **Shift Left Security** for the open-source application **Conduit** — a Medium.com clone built with Flask.

**Target Application (Application Cible) :**
- **Repo:** [gothinkster/flask-realworld-example-app](https://github.com/gothinkster/flask-realworld-example-app)
- **Commit:** `4b95fb2227dfeb5dd1a45d89b2bf48630b93fd28`
- **License:** MIT
- **Language:** Python 3 (Flask)
- **Features:** JWT authentication, SQLAlchemy ORM, PostgreSQL, REST API, pytest suite

> **Local clone:** The target app was cloned into `target-app/` (gitignored) for local SAST/DAST analysis. The pipeline clones it fresh from GitHub in Stage 1 on every run.

On every push, the pipeline runs 9 stages:

| Stage | What | Tool |
|-------|------|------|
| 1 | Source retrieval & integrity | git + Gitleaks |
| 2 | Build | pip install |
| 3 | Code quality | SonarQube Community |
| 4 | Unit tests & coverage | pytest + coverage.py |
| 5 | SAST | Semgrep + Bandit + Gitleaks + pip-audit |
| 6 | Container build & scan | Docker + Trivy |
| 7 | Deploy to test env | docker compose |
| 8 | DAST | OWASP ZAP + 12 custom scenarios |
| 9 | Report generation | aggregate_reports.py |

## Real Findings / Résultats Réels

Our analysis found **20 security issues** in the target app:

| Severity | Count | Top Finding |
|----------|-------|-------------|
| 🔴 CRITICAL | 1 | Default SECRET_KEY — JWT forgery possible |
| 🔴 HIGH | 5 | SQLAlchemy CVEs, no rate limiting, no TLS |
| 🟡 MEDIUM | 8 | Missing HSTS, no jti, no account lockout |
| 🟢 LOW | 6 | Long JWT expiry, CLI subprocess usage |

Full details: [docs/06-findings.md](docs/06-findings.md) | [docs/07-recommendations.md](docs/07-recommendations.md)

## Quickstart

```bash
# Prerequisites: Ubuntu 22.04, Docker, make, git
git clone https://github.com/bailimohammed799-dot/devsecops-pipeline.git
cd devsecops-pipeline

# One-time setup
make setup

# Run the full pipeline
make pipeline

# Browse reports
ls reports/$(ls -1t reports/ | head -1)/
```

## Documentation

| Document | Contents |
|----------|----------|
| [00-architecture.md](docs/00-architecture.md) | Pipeline diagram + data flow |
| [01-target-app.md](docs/01-target-app.md) | Target application selection & rationale |
| [02-pipeline-stages.md](docs/02-pipeline-stages.md) | Detailed stage-by-stage breakdown |
| [03-tooling.md](docs/03-tooling.md) | Every tool, version, config |
| [04-reports.md](docs/04-reports.md) | How to read reports |
| [05-reproduction.md](docs/05-reproduction.md) | Step-by-step from fresh clone |
| [06-findings.md](docs/06-findings.md) | All vulnerabilities found |
| [07-recommendations.md](docs/07-recommendations.md) | Prioritized remediation plan |
| [decisions.md](docs/decisions.md) | Architecture Decision Records |

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required: `TARGET_COMMIT`, `SONAR_HOST_URL`, `SONAR_TOKEN`, `SECRET_KEY`

## Project Structure

```
devsecops-pipeline/
├── .github/workflows/   # ci.yml + cd.yml + nightly.yml
├── docker/              # Multi-stage Dockerfile + compose (4 services)
├── scripts/             # 9 shell scripts + 1 Python aggregator
├── tests/security/      # 12 custom DAST scenario scripts
├── docs/                # 9 documentation files (English)
├── reports/
│   ├── demo-20260622/   # Sample run with real findings
│   └── french/          # Prompts for French internship reports
├── target-app/          # Local clone of gothinkster/flask-realworld-example-app (gitignored)
├── Makefile             # setup / pipeline / clean / reports
├── Jenkinsfile          # Equivalent pipeline for Jenkins
└── README.md
```

## License

MIT
