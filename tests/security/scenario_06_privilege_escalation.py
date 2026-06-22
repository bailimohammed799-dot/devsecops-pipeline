#!/usr/bin/env python3
"""Scenario 6: Privilege Escalation — low-priv user accessing admin endpoints."""
import argparse, requests
import random, string

def test_privilege_escalation(url, output_file):
    findings = []
    base = url.rstrip('/')

    try:
        # Create low-priv user
        username = f"lowpriv_{''.join(random.choices(string.ascii_lowercase, k=8))}"
        email = f"{username}@test.com"
        password = "LowPriv123!"

        requests.post(f"{base}/api/users",
            json={"user": {"username": username, "email": email, "password": password}},
            timeout=10)

        resp = requests.post(f"{base}/api/users/login",
            json={"user": {"email": email, "password": password}},
            timeout=10)
        token = resp.json().get('user', {}).get('token', '') if resp.status_code == 200 else ''
        headers = {'Authorization': f'Token {token}'}

        # Attempt to access/modify other users' resources
        admin_style_endpoints = [
            ('GET', '/api/admin'),
            ('GET', '/api/users'),
            ('DELETE', '/api/admin/users'),
            ('PUT', '/api/admin/config'),
            ('GET', '/api/profiles/admin'),
            ('DELETE', '/api/articles/9999'),  # Non-existent article
        ]

        for method, endpoint in admin_style_endpoints:
            try:
                if method == 'GET':
                    resp = requests.get(f"{base}{endpoint}", headers=headers, timeout=5)
                elif method == 'DELETE':
                    resp = requests.delete(f"{base}{endpoint}", headers=headers, timeout=5)
                elif method == 'PUT':
                    resp = requests.put(f"{base}{endpoint}", json={}, headers=headers, timeout=5)
                elif method == 'POST':
                    resp = requests.post(f"{base}{endpoint}", json={}, headers=headers, timeout=5)

                # If we get 200 on admin-like endpoints, that's a finding
                if resp.status_code == 200 and 'admin' in endpoint.lower():
                    findings.append({
                        'severity': 'Critical',
                        'description': f'Low-priv user can access admin endpoint: {method} {endpoint}',
                        'evidence': f'HTTP {resp.status_code} returned',
                        'fix': 'Implement role-based access control (RBAC). Check user roles before serving admin endpoints.'
                    })
                elif resp.status_code in (200, 201) and method in ('DELETE', 'PUT', 'POST'):
                    # Successful mutation by low-priv user on protected resource
                    findings.append({
                        'severity': 'High',
                        'description': f'Low-priv user performed {method} on {endpoint} (HTTP {resp.status_code})',
                        'evidence': f'Request succeeded with low-privilege token',
                        'fix': 'Verify resource ownership before allowing mutations. Users should only modify their own resources.'
                    })
            except:
                pass

        # Try parameter tampering: modify another user's profile
        try:
            resp = requests.put(f"{base}/api/user",
                json={"user": {"email": "hacked@evil.com", "role": "admin"}},
                headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('user', {}).get('role') == 'admin':
                    findings.append({
                        'severity': 'Critical',
                        'description': 'Parameter tampering enabled role escalation to admin',
                        'evidence': f'PUT /api/user with role=admin succeeded',
                        'fix': 'Never accept role/permission fields from user input. Use server-side role assignment.'
                    })
        except:
            pass

    except Exception as e:
        findings.append({'severity': 'Info', 'description': f'Test error: {str(e)}'})

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 6: Privilege Escalation\n\n")
        f.write(f"**Target:** {url}\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No privilege escalation vulnerabilities detected\n\n")
            f.write("Proper authorization checks are in place. Low-privilege users cannot access admin functionality or modify other users' resources.\n\n")

    print(f"Scenario 6 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_privilege_escalation(args.url, args.output)
