# 07 — Recommendations

Prioritized remediation backlog based on all findings in `docs/06-findings.md`.

## Priority Definitions

| Priority | Action | Timeline |
|----------|--------|----------|
| **P0 — Critical** | Fix immediately | Now — blocking deployment |
| **P1 — High** | Fix this sprint | 1-2 weeks |
| **P2 — Medium** | Fix next sprint | 2-4 weeks |
| **P3 — Low** | Backlog | When time permits |

---

## P0 — Fix Now (Critical)

> *Populated from pipeline findings. Items here block production deployment.*

| ID | Finding | Linked Finding |
|----|---------|----------------|
| — | *Run pipeline to populate* | — |

---

## P1 — This Sprint (High)

> *Address within the current development sprint.*

| ID | Finding | Linked Finding |
|----|---------|----------------|
| — | *Run pipeline to populate* | — |

---

## P2 — Next Sprint (Medium)

> *Schedule for the next sprint. Not urgent but reduces risk.*

| ID | Finding | Linked Finding |
|----|---------|----------------|
| — | *Run pipeline to populate* | — |

---

## P3 — Backlog (Low / Info)

> *Address when time permits. Informational or defense-in-depth items.*

| ID | Finding | Linked Finding |
|----|---------|----------------|
| — | *Run pipeline to populate* | — |

---

## General Recommendations

Regardless of specific findings, these are always recommended for the target application:

### Password Policy
- Enforce minimum 8 characters, mixed case, numbers, special characters
- Implement password strength meter in the UI
- Add account lockout after 5 failed attempts

### Authentication
- Implement rate limiting on `/api/users/login` (5 attempts/minute/IP)
- Add JWT token expiry (currently handled by Flask-JWT-Extended — verify)
- Implement token refresh mechanism
- Consider adding MFA for admin accounts

### API Security
- Add request size limits (`app.config['MAX_CONTENT_LENGTH']`)
- Implement idempotency keys for mutation endpoints
- Add CORS restrictions to known origins only
- Add API versioning (`/api/v1/`)

### Infrastructure
- Deploy behind a reverse proxy (Nginx/Traefik) with TLS termination
- Add security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- Use secrets management (HashiCorp Vault, AWS Secrets Manager)
- Implement centralized logging and monitoring

### Dependency Management
- Run `pip-audit` on every PR
- Pin dependency versions with hashes
- Set up Dependabot or Renovate for automated updates
- Review and remove unused dependencies
