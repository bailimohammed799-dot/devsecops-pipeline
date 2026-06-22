# 06 — Findings

All vulnerabilities discovered across pipeline runs. Each finding includes evidence, impact, and a recommended fix.

> **Note:** This document is populated after pipeline execution. Run `make pipeline` to generate initial findings, or refer to `reports/<run>/SUMMARY.md` for the latest results.

---

## Finding Inventory

| ID | Tool | Scenario | Severity | Status | Description |
|----|------|----------|----------|--------|-------------|
| F-001 | Semgrep | SAST | — | 🔴 Open | *Populated after pipeline run* |
| F-002 | Bandit | SAST | — | 🔴 Open | *Populated after pipeline run* |
| F-003 | Gitleaks | Secret Scan | — | 🔴 Open | *Populated after pipeline run* |
| F-004 | pip-audit | Dependency | — | 🔴 Open | *Populated after pipeline run* |
| F-005 | Trivy | Container | — | 🔴 Open | *Populated after pipeline run* |
| F-006 | ZAP | DAST | — | 🔴 Open | *Populated after pipeline run* |

---

## Template for Each Finding

When populating after a pipeline run, use this format:

```markdown
### F-XXX: [Brief Title]

- **Tool:** Semgrep / Bandit / ZAP / Trivy / ...
- **Scenario:** SAST / SQL Injection / Sensitive Data Exposure / ...
- **Severity:** Critical / High / Medium / Low / Info
- **CVSS v3.1 Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H (if applicable)
- **File:** `path/to/file.py:123`
- **Evidence:**
  ```
  [Request/response or code snippet showing the vulnerability]
  ```
- **Description:** What the vulnerability is and how an attacker could exploit it.
- **Business Impact:** What happens if exploited — data loss, account takeover, service disruption, etc.
- **Recommended Fix:**
  ```
  [Code example or configuration change]
  ```
- **Fix Difficulty:** S (Small — 1 line) / M (Medium — 1 file) / L (Large — architectural)
```

---

## Reference Run

After a complete pipeline run, paste the final `SUMMARY.md` content here as an appendix.

```markdown
<!-- INSERT SUMMARY.md CONTENT HERE AFTER RUN -->
```
