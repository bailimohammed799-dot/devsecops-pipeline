# 06 — Findings

All vulnerabilities discovered by the DevSecOps pipeline. Each finding includes evidence, impact, and a recommended fix.

> **Reference Run:** `demo-20260622` — Source code analysis on Windows (SAST + DAST scenario analysis).
> Full results: `reports/demo-20260622/`

---

## Finding Inventory

| ID | Tool | Scenario | Severity | Status | Description |
|----|------|----------|----------|--------|-------------|
| F-001 | pip-audit | SAST — Dependency | 🔴 HIGH | Open | SQLAlchemy 1.1.9: CVE-2019-7164 (SQLi via order_by) |
| F-002 | pip-audit | SAST — Dependency | 🔴 HIGH | Open | SQLAlchemy 1.1.9: CVE-2019-7548 (SQLi via group_by) |
| F-003 | Bandit | SAST — Python | 🟡 LOW | Open | subprocess module imported (commands.py:5) |
| F-004 | Bandit | SAST — Python | 🟡 LOW | Open | subprocess.call() used (commands.py:41) |
| F-005 | Code Review | 10 — Security Misconfig | 🔴 CRITICAL | Open | Default SECRET_KEY='secret-key' in settings.py |
| F-006 | Code Review | 2 — MITM | 🔴 HIGH | Open | No TLS/SSL — app served over HTTP only |
| F-007 | Code Review | 3 — Broken Auth | 🔴 HIGH | Open | No rate limiting on /api/users/login |
| F-008 | Code Review | 9 — Credential Stuffing | 🔴 HIGH | Open | Brute-force possible due to missing rate limiting |
| F-009 | Code Review | 3 — Broken Auth | 🟡 MEDIUM | Open | No password complexity requirements |
| F-010 | Code Review | 3 — Broken Auth | 🟡 MEDIUM | Open | No account lockout mechanism |
| F-011 | Code Review | 2 — MITM | 🟡 MEDIUM | Open | Missing HSTS header |
| F-012 | Code Review | 5 — Replay Attack | 🟡 MEDIUM | Open | JWT lacks jti (unique token ID) claim |
| F-013 | Code Review | 7 — API Abuse | 🟡 MEDIUM | Open | No MAX_CONTENT_LENGTH (request size limit) |
| F-014 | Code Review | 8 — DoS | 🟡 MEDIUM | Open | No request timeout/size configuration |
| F-015 | Code Review | 1 — SQL Injection | 🟡 MEDIUM | Open | order_by() used — verify static column usage |
| F-016 | Code Review | 3 — Broken Auth | 🟢 LOW | Open | JWT expiry: ~11.5 days in dev mode |
| F-017 | Code Review | 4 — Session Hijacking | 🟢 LOW | Open | No JWT token revocation/blacklist |
| F-018 | Code Review | 5 — Replay Attack | 🟢 LOW | Open | No idempotency keys on mutation endpoints |
| F-019 | Code Review | 10 — Security Misconfig | 🟡 MEDIUM | Open | DEBUG=True in DevConfig |
| F-020 | Code Review | 12 — Sender Spoofing | ⚪ N/A | N/A | App has no email/SMS features |

---

## Critical Findings

### F-005: Default SECRET_KEY Allows JWT Forgery

- **Tool:** Code Review (Manual)
- **Scenario:** Security Misconfiguration (#10)
- **Severity:** 🔴 CRITICAL
- **CVSS v3.1:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H (9.8)
- **File:** `conduit/settings.py:10`
- **Evidence:**
  ```python
  SECRET_KEY = os.environ.get('CONDUIT_SECRET', 'secret-key')  # TODO: Change me
  ```
- **Description:** If the `CONDUIT_SECRET` environment variable is not set, the application uses the hardcoded string `'secret-key'` as its JWT signing key. An attacker who knows this key can forge valid JWT tokens for any user, gaining full account takeover.
- **Business Impact:** Complete authentication bypass. Attacker can impersonate any user, access private data, create/delete articles, and modify profiles.
- **Recommended Fix:**
  ```python
  SECRET_KEY = os.environ.get('CONDUIT_SECRET')
  if not SECRET_KEY:
      raise RuntimeError("CONDUIT_SECRET environment variable must be set")
  ```
- **Fix Difficulty:** S (Small — 3 lines)

---

## High Findings

### F-001 & F-002: SQLAlchemy 1.1.9 SQL Injection CVEs

- **Tool:** pip-audit
- **Scenario:** SAST — Dependency Scanning
- **Severity:** 🔴 HIGH
- **CVSS v3.1:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H (9.8 for CVE-2019-7164)
- **Dependency:** `SQLAlchemy==1.1.9` (2017 release)
- **Evidence:**
  ```
  CVE-2019-7164: SQL injection via order_by parameter
  CVE-2019-7548: SQL injection via group_by parameter
  ```
- **Description:** SQLAlchemy versions before 1.3.0b3 allow SQL injection when attacker-controlled strings are passed to `order_by()` or `group_by()`. The fix was never backported to the 1.2.x line.
- **Status:** In the current code, `order_by(Article.createdAt.desc())` uses a **static column reference** — not directly exploitable. However, any future code that passes user input to `order_by()` or `group_by()` will be immediately vulnerable.
- **Business Impact:** If exploited, full database compromise — data theft, modification, or deletion.
- **Recommended Fix:** Upgrade `SQLAlchemy` to `>= 2.0.0`. Test all queries after upgrade.
- **Fix Difficulty:** M (Medium — dependency upgrade requires testing)

### F-006: No TLS — HTTP Only

- **Tool:** Code Review
- **Scenario:** MITM (#2)
- **Severity:** 🔴 HIGH
- **Description:** The application is served over plain HTTP with no TLS/SSL configuration. All traffic — including JWT tokens and passwords — travels in cleartext.
- **Fix:** Deploy behind Nginx with TLS termination. Use Let's Encrypt for free certificates.

### F-007 & F-008: No Rate Limiting on Authentication

- **Tool:** Code Review
- **Scenario:** Broken Authentication (#3), Credential Stuffing (#9)
- **Severity:** 🔴 HIGH
- **Description:** No rate limiting on `/api/users/login`. Attackers can perform unlimited brute-force or credential stuffing attempts.
- **Fix:** Implement Flask-Limiter: 5 requests per minute per IP on login endpoint.

---

## Findings by Scenario (DAST)

| # | Scenario | Findings | Top Severity |
|---|----------|----------|-------------|
| 1 | SQL Injection | 2 | HIGH |
| 2 | MITM | 2 | HIGH |
| 3 | Broken Authentication | 3 | HIGH |
| 4 | Session Hijacking | 2 | LOW |
| 5 | Replay Attack | 2 | MEDIUM |
| 6 | Privilege Escalation | 2 | INFO |
| 7 | API Abuse | 2 | MEDIUM |
| 8 | Denial of Service | 1 | MEDIUM |
| 9 | Credential Stuffing | 1 | HIGH |
| 10 | Security Misconfiguration | 2 | CRITICAL |
| 11 | Sensitive Data Exposure | 3 | INFO |
| 12 | Sender Spoofing | 0 | N/A |

---

## Positive Findings (What's Done Right)

1. ✅ **Password hashing:** Uses Flask-Bcrypt with bcrypt algorithm (13 rounds in production)
2. ✅ **SQLAlchemy ORM:** All queries use parameterized ORM methods — strong SQL injection protection
3. ✅ **Resource ownership:** Article updates/deletes check `author_id == current_user`
4. ✅ **Password in responses:** `load_only=True` prevents password from appearing in API responses
5. ✅ **JWT authentication:** Uses Flask-JWT-Extended with proper `@jwt_required` decorators
6. ✅ **Semgrep clean:** 156 rules on 21 files — zero OWASP Top 10 findings
