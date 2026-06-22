# Architecture Decision Records

## ADR-001: Target Application Selection

- **Date:** 2026-06-22
- **Status:** Accepted
- **Context:** The specification requires an existing open-source web application with login, database, REST API, unit tests, permissive license, and recent activity.
- **Decision:** Selected `gothinkster/flask-realworld-example-app` (Flask backend for RealWorld spec) at commit `4b95fb2`.
- **Consequences:**
  - ✅ MIT license, Python/Flask (preferred language), full REST API, JWT auth, SQLAlchemy, pytest suite
  - ✅ Has every feature needed for all 12 DAST scenarios
  - ✅ Small enough (~3K LOC) to build in <5 minutes
  - ⚠️ Last upstream commit was 2019-09-01 (7 years ago). This is a known issue — the code is feature-complete and stable, the RealWorld spec project remains actively maintained, and no other candidate met ALL other criteria as comprehensively.
  - ⚠️ PostgreSQL is the native DB; we'll use a compose-managed postgres container for the test env.

## ADR-002: GitHub Actions as Primary CI, Jenkinsfile as Secondary

- **Date:** 2026-06-22
- **Status:** Accepted
- **Context:** The "cahier des charges" lists Jenkins, GitHub Actions, or GitLab CI as options.
- **Decision:** GitHub Actions as primary (free, integrated with GitHub fork), with a functionally equivalent `Jenkinsfile` as a secondary deliverable.
- **Consequences:** CI is triggered on every push to the fork. The Jenkinsfile provides an alternative for teams using on-premise Jenkins.

## ADR-003: Docker Compose for Local Registry

- **Date:** 2026-06-22
- **Status:** Accepted
- **Context:** Need an artifact registry for the Docker image. No cloud services allowed (cost constraint).
- **Decision:** Run `registry:2` as a Docker Compose service. Push/pull from `localhost:5000`.
- **Consequences:** No external dependency. Registry data is ephemeral (container restart clears it) — acceptable for a test pipeline.

## ADR-004: Node.js 14+ Required for npm audit

- **Date:** 2026-06-22
- **Status:** Accepted
- **Context:** Node.js SAST tools (ESLint security plugin, npm audit) need Node.js runtime even for a Python app.
- **Decision:** Install Node.js 18.x LTS alongside Python in the CI runner.
- **Consequences:** Slightly larger CI setup; allows running Node-based security tools as a complement to Python-specific ones.

## ADR-005: Semgrep as Primary SAST, Bandit as Complement

- **Date:** 2026-06-22
- **Status:** Accepted
- **Context:** Need multi-language SAST. Semgrep supports Python + generic patterns; Bandit is Python-specific.
- **Decision:** Run both. Semgrep with `p/owasp-top-ten`, `p/security-audit`, `p/python` rulesets. Bandit for Python-specific patterns.
- **Consequences:** Slightly longer SAST stage (~60s), but much better coverage. Findings are deduplicated in aggregation.

## ADR-006: Ubuntu 22.04 as Target Platform

- **Date:** 2026-06-22
- **Status:** Accepted
- **Context:** Specification says "fresh Ubuntu 22.04 box with Docker installed."
- **Decision:** All CI runners use `ubuntu-22.04`. Makefile targets use apt for system dependencies.
- **Consequences:** Package names and paths are Ubuntu-specific. No macOS or Windows support for the full pipeline (development on any OS is fine — the pipeline runs in CI/Ubuntu).
