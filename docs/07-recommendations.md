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

| ID | Finding | Linked |
|----|---------|--------|
| P0-1 | Default SECRET_KEY='***' in settings.py — JWT forgery possible | [F-005](06-findings.md#f-005-default-secret_key-allows-jwt-forgery) |

**Action:** Remove default fallback value. Require `CONDUIT_SECRET` env var:
```python
SECRET_KEY=os.env...')
if not SECRET_KEY:
    raise RuntimeError("CONDUIT_SECRET must be set")
```

---

## P1 — This Sprint (High)

| ID | Finding | Linked |
|----|---------|--------|
| P1-1 | SQLAlchemy 1.1.9 — CVE-2019-7164, CVE-2019-7548 | [F-001](06-findings.md), [F-002](06-findings.md) |
| P1-2 | No rate limiting on login endpoint | [F-007](06-findings.md), [F-008](06-findings.md) |
| P1-3 | No TLS — HTTP only, credentials in cleartext | [F-006](06-findings.md) |

**Actions:**
1. Upgrade `SQLAlchemy>=2.0` in `requirements/prod.txt`. Run full test suite.
2. Add `Flask-Limiter`: 5 req/min/IP on `/api/users/login`
3. Deploy Nginx reverse proxy with Let's Encrypt TLS

---

## P2 — Next Sprint (Medium)

| ID | Finding | Linked |
|----|---------|--------|
| P2-1 | No password complexity requirements | [F-009](06-findings.md) |
| P2-2 | No account lockout mechanism | [F-010](06-findings.md) |
| P2-3 | Missing HSTS header | [F-011](06-findings.md) |
| P2-4 | JWT lacks jti claim | [F-012](06-findings.md) |
| P2-5 | No MAX_CONTENT_LENGTH | [F-013](06-findings.md) |

**Actions:**
1. Enforce min 8 chars, mixed case, numbers in password validation
2. Lock account 15 min after 5 failed login attempts
3. Add `Strict-Transport-Security: max-age=31536000` header
4. Add unique `jti` claim to JWT tokens
5. Set `app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024`

---

## P3 — Backlog (Low / Info)

| ID | Finding | Linked |
|----|---------|--------|
| P3-1 | JWT expiry too long in dev (~11.5 days) | [F-016](06-findings.md) |
| P3-2 | No JWT revocation/blacklist | [F-017](06-findings.md) |
| P3-3 | No idempotency keys on mutations | [F-018](06-findings.md) |
| P3-4 | DEBUG=True in DevConfig | [F-019](06-findings.md) |
| P3-5 | CORS whitelist too broad in production | — |

---

## General Recommendations

### Password Policy
- Enforce minimum 8 characters, mixed case, numbers, special characters
- Implement password strength meter in the UI
- Add account lockout after 5 failed attempts

### Authentication
- Implement rate limiting on `/api/users/login` (5 attempts/minute/IP)
- Set JWT access token expiry to 15-60 minutes in production
- Implement token refresh mechanism
- Add unique `jti` claim to prevent replay

### API Security
- Add `MAX_CONTENT_LENGTH` (1 MB)
- Implement idempotency keys for mutation endpoints
- Restrict CORS to production frontend origin only
- Add API versioning (`/api/v1/`)

### Infrastructure
- Deploy behind Nginx with TLS termination (Let's Encrypt)
- Add security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- Use secrets management (env vars, never hardcoded)
- Implement centralized logging and monitoring

### Dependency Management
- Upgrade SQLAlchemy from 1.1.9 to ≥2.0
- Run `pip-audit` on every PR
- Pin dependency versions with hashes
- Set up Dependabot for automated updates
