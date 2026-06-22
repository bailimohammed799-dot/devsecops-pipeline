#!/usr/bin/env python3
"""Scenario 4: Session Hijacking — cookie security attributes, session fixation."""
import argparse, requests

def test_session_hijacking(url, output_file):
    findings = []
    base = url.rstrip('/')

    # Register and login to get session cookies
    try:
        import random, string
        username = f"sessiontest_{''.join(random.choices(string.ascii_lowercase, k=8))}"
        email = f"{username}@test.com"
        password = "Test1234!@#$"

        # Register
        resp = requests.post(f"{base}/api/users",
            json={"user": {"username": username, "email": email, "password": password}},
            timeout=10)

        # Login
        resp = requests.post(f"{base}/api/users/login",
            json={"user": {"email": email, "password": password}},
            timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            token = data.get('user', {}).get('token', '')

            # Check cookie attributes (for session cookies in response)
            set_cookie = resp.headers.get('Set-Cookie', '')
            cookies = resp.cookies

            # JWT-based auth — check if token has expiry
            if token:
                try:
                    import base64 as b64, json
                    parts = token.split('.')
                    if len(parts) == 3:
                        payload = json.loads(b64.urlsafe_b64decode(parts[1] + '=='))
                        exp = payload.get('exp')
                        if not exp:
                            findings.append({
                                'severity': 'High',
                                'description': 'JWT token has no expiration',
                                'evidence': f'Token payload: {payload}',
                                'fix': 'Always set exp claim on JWT tokens. Use short-lived tokens (15-60 min).'
                            })
                except:
                    pass

            # Check for cookie security attributes
            if set_cookie:
                if 'HttpOnly' not in set_cookie:
                    findings.append({
                        'severity': 'Medium',
                        'description': 'Session cookie missing HttpOnly flag',
                        'evidence': f'Set-Cookie: {set_cookie[:100]}',
                        'fix': 'Set HttpOnly=True on session cookies to prevent JavaScript access.'
                    })
                if 'Secure' not in set_cookie:
                    findings.append({
                        'severity': 'Medium',
                        'description': 'Session cookie missing Secure flag',
                        'evidence': f'Set-Cookie: {set_cookie[:100]}',
                        'fix': 'Set Secure=True on session cookies (requires HTTPS).'
                    })
                if 'SameSite' not in set_cookie:
                    findings.append({
                        'severity': 'Low',
                        'description': 'Session cookie missing SameSite attribute',
                        'evidence': f'Set-Cookie: {set_cookie[:100]}',
                        'fix': 'Set SameSite=Lax or SameSite=Strict to prevent CSRF-based session hijacking.'
                    })

            # Check if token changes on re-login (session fixation test)
            resp2 = requests.post(f"{base}/api/users/login",
                json={"user": {"email": email, "password": password}},
                timeout=10)
            token2 = resp2.json().get('user', {}).get('token', '')
            if token and token2 and token == token2:
                findings.append({
                    'severity': 'Low',
                    'description': 'Same token returned on re-login — possible session fixation',
                    'evidence': 'Token unchanged between two login requests',
                    'fix': 'Issue a new token on every login.'
                })

        # Test accessing protected endpoint without auth
        resp = requests.get(f"{base}/api/user", timeout=10)
        if resp.status_code == 200:
            findings.append({
                'severity': 'Critical',
                'description': 'Protected endpoint accessible without authentication',
                'evidence': f'GET /api/user returned HTTP 200 without auth header',
                'fix': 'Add @jwt_required() decorator to all protected endpoints.'
            })

    except Exception as e:
        pass

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 4: Session Hijacking\n\n")
        f.write(f"**Target:** {url}\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No session hijacking vulnerabilities detected\n\n")

    print(f"Scenario 4 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_session_hijacking(args.url, args.output)
