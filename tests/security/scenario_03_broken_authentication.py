#!/usr/bin/env python3
"""Scenario 3: Broken Authentication — weak passwords, default creds, missing rate limiting."""
import argparse, requests, time

def test_broken_auth(url, output_file):
    findings = []
    base = url.rstrip('/')

    # Test 1: Weak passwords
    weak_passwords = ['password', '123456', 'admin', 'test', 'password1', 'qwerty', 'letmein']
    for pw in weak_passwords:
        try:
            resp = requests.post(f"{base}/api/users",
                json={"user": {"username": f"weaktest_{pw}", "email": f"weak_{pw}@test.com", "password": pw}},
                timeout=10)
            # If the app accepts very weak passwords
            if resp.status_code in (200, 201):
                findings.append({
                    'severity': 'Medium',
                    'description': f'Application accepts weak password: "{pw}"',
                    'evidence': f'Registration succeeded with password "{pw}" (HTTP {resp.status_code})',
                    'fix': 'Enforce password policy: minimum 8 chars, mixed case, numbers, special characters.'
                })
                break
        except:
            pass

    # Test 2: Default credentials
    default_creds = [
        ('admin@admin.com', 'admin'),
        ('admin@conduit.com', 'password'),
        ('test@test.com', 'test'),
    ]
    for email, pw in default_creds:
        try:
            resp = requests.post(f"{base}/api/users/login",
                json={"user": {"email": email, "password": pw}},
                timeout=10)
            if resp.status_code == 200:
                findings.append({
                    'severity': 'Critical',
                    'description': f'Default credentials work: {email} / {pw}',
                    'evidence': f'Login succeeded with {email}:{pw}',
                    'fix': 'Remove or disable default accounts. Force password change on first login.'
                })
        except:
            pass

    # Test 3: Rate limiting on login
    try:
        rapid_attempts = 0
        for i in range(20):
            resp = requests.post(f"{base}/api/users/login",
                json={"user": {"email": f"ratelimit_{i}@test.com", "password": "wrong"}},
                timeout=5)
            rapid_attempts += 1
            if resp.status_code == 429:
                break
        if rapid_attempts >= 20:
            findings.append({
                'severity': 'High',
                'description': 'No rate limiting on login endpoint — brute force possible',
                'evidence': f'{rapid_attempts} rapid login attempts without 429 response',
                'fix': 'Implement rate limiting (e.g., Flask-Limiter) on /api/users/login: 5 attempts per minute per IP.'
            })
    except:
        pass

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 3: Broken Authentication\n\n")
        f.write(f"**Target:** {url}\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No broken authentication issues detected\n\n")

    print(f"Scenario 3 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_broken_auth(args.url, args.output)
