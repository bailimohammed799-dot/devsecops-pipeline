#!/usr/bin/env python3
"""Scenario 9: Credential Stuffing — test leaked credentials, check rate limiting/MFA."""
import argparse, requests, time

def test_credential_stuffing(url, output_file):
    findings = []
    base = url.rstrip('/')

    # Small list of commonly leaked credentials
    leaked_creds = [
        ("admin@admin.com", "admin"),
        ("admin@admin.com", "password"),
        ("user@example.com", "password123"),
        ("test@example.com", "test123"),
        ("root@localhost", "root"),
        ("administrator@conduit.com", "administrator"),
        ("demo@demo.com", "demo"),
        ("guest@guest.com", "guest"),
        ("info@conduit.com", "conduit123"),
        ("support@conduit.com", "support"),
    ]

    successful_logins = []
    rate_limited = False
    start_time = time.time()

    for email, password in leaked_creds:
        try:
            resp = requests.post(f"{base}/api/users/login",
                json={"user": {"email": email, "password": password}},
                timeout=10)

            if resp.status_code == 429:
                rate_limited = True
                break

            if resp.status_code == 200:
                successful_logins.append((email, password))
        except:
            pass

    elapsed = time.time() - start_time

    if successful_logins:
        findings.append({
            'severity': 'Critical',
            'description': f'Credential stuffing succeeded — {len(successful_logins)} accounts compromised',
            'evidence': f'Successful logins: {successful_logins}',
            'fix': 'Implement account lockout after 5 failed attempts. Add CAPTCHA after 3 failed attempts. Require MFA.'
        })

    if not rate_limited:
        attempts_per_second = len(leaked_creds) / max(elapsed, 0.1)
        findings.append({
            'severity': 'High',
            'description': f'No rate limiting detected — {len(leaked_creds)} attempts in {elapsed:.1f}s ({attempts_per_second:.1f}/s)',
            'evidence': f'All {len(leaked_creds)} credential attempts processed without 429 response',
            'fix': 'Add Flask-Limiter or fail2ban: limit /api/users/login to 5 requests per minute per IP.'
        })

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 9: Credential Stuffing\n\n")
        f.write(f"**Target:** {url}\n")
        f.write(f"**Tested:** {len(leaked_creds)} common leaked credentials\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No credential stuffing vulnerabilities detected\n\n")
            f.write("Rate limiting and/or account lockout is properly configured.\n\n")

    print(f"Scenario 9 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_credential_stuffing(args.url, args.output)
