# DevSecOps Pipeline — Quickstart

> **Summer Internship Project:** Complete DevSecOps pipeline with Shift Left Security for a Flask web application.

[![CI](https://github.com/USER/devsecops-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/USER/devsecops-pipeline/actions/workflows/ci.yml)
[![CD](https://github.com/USER/devsecops-pipeline/actions/workflows/cd.yml/badge.svg)](https://github.com/USER/devsecops-pipeline/actions/workflows/cd.yml)
[![Nightly](https://github.com/USER/devsecops-pipeline/actions/workflows/nightly.yml/badge.svg)](https://github.com/USER/devsecops-pipeline/actions/workflows/nightly.yml)

## What This Is

A complete, reproducible DevSecOps pipeline implementing **Shift Left Security** for `gothinkster/flask-realworld-example-app` (Conduit — a Medium.com clone). On every push, the pipeline runs:

| Stage | What | Tool |
|-------|------|------|
| 1 | Source retrieval & integrity | git + Gitleaks |
| 2 | Build | pip install |
| 3 | Code quality | SonarQube Community |
| 4 | Unit tests & coverage | pytest + coverage.py |
| 5 | SAST | Semgrep + Bandit + Gitleaks + Dependency-Check |
| 6 | Container build & scan | Docker + Trivy |
| 7 | Deploy to test env | docker compose |
| 8 | DAST | OWASP ZAP + 12 custom scenarios |
| 9 | Report generation | aggregate_reports.py |

## Quickstart

```bash
# Prerequisites: Ubuntu 22.04, Docker, make, git
git clone https://github.com/USER/devsecops-pipeline.git
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

## License

MIT — see [LICENSE](LICENSE)
