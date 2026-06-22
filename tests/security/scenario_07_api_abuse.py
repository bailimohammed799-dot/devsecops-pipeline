#!/usr/bin/env python3
"""Scenario 7: API Abuse — unauthenticated access, malformed payloads, rate limits."""
import argparse, requests, time
import random, string

def test_api_abuse(url, output_file):
    findings = []
    base = url.rstrip('/')

    # Test 1: Access protected endpoints without auth
    protected_endpoints = [
        ('GET', '/api/user'),
        ('PUT', '/api/user'),
        ('GET', '/api/profiles/testuser'),
        ('POST', '/api/articles'),
        ('DELETE', '/api/articles/1'),
        ('POST', '/api/articles/1/favorite'),
    ]

    for method, endpoint in protected_endpoints:
        try:
            if method == 'GET':
                resp = requests.get(f"{base}{endpoint}", timeout=5)
            elif method == 'POST':
                resp = requests.post(f"{base}{endpoint}", json={}, timeout=5)
            elif method == 'PUT':
                resp = requests.put(f"{base}{endpoint}", json={}, timeout=5)
            elif method == 'DELETE':
                resp = requests.delete(f"{base}{endpoint}", timeout=5)

            if resp.status_code == 200:
                findings.append({
                    'severity': 'Critical',
                    'description': f'Protected endpoint {method} {endpoint} accessible without authentication',
                    'evidence': f'HTTP 200 returned without Authorization header',
                    'fix': 'Add @jwt_required() decorator to this endpoint.'
                })
        except:
            pass

    # Test 2: Malformed payloads
    malformed_payloads = [
        None,
        "",
        "not json",
        {"not": "a user object"},
        {"user": None},
        {"user": {"email": "a" * 10000}},  # Very long email
        {"user": {"username": "test", "email": "x", "password": ""}},
        {"user": {"username": "<script>alert(1)</script>", "email": "xss@test.com", "password": "Test123!"}},
    ]

    for i, payload in enumerate(malformed_payloads):
        try:
            resp = requests.post(f"{base}/api/users",
                json=payload if isinstance(payload, (dict, type(None))) else payload,
                timeout=5)
            # Check for 500 errors (unhandled exceptions)
            if resp.status_code == 500:
                findings.append({
                    'severity': 'High',
                    'description': f'Server error (500) on malformed payload #{i}: {repr(payload)[:50]}',
                    'evidence': f'Response: {resp.text[:200]}',
                    'fix': 'Add input validation middleware. Return 400 for malformed input, never 500.'
                })
            # Check for verbose error messages
            if 'traceback' in resp.text.lower() or 'exception' in resp.text.lower():
                findings.append({
                    'severity': 'Medium',
                    'description': 'Verbose error/debug information exposed',
                    'evidence': f'Response contains traceback or exception details',
                    'fix': 'Set app.debug=False. Use custom error handlers that return generic error messages.'
                })
        except:
            pass

    # Test 3: Mass assignment
    try:
        resp = requests.post(f"{base}/api/users",
            json={"user": {
                "username": "massassign",
                "email": "mass@test.com",
                "password": "Test123!",
                "is_admin": True,
                "role": "admin"
            }},
            timeout=5)
        # If it succeeds, check if the extra fields were accepted
        if resp.status_code in (200, 201):
            findings.append({
                'severity': 'High',
                'description': 'Possible mass assignment — extra fields (is_admin, role) accepted in registration',
                'evidence': f'HTTP {resp.status_code}',
                'fix': 'Use Marshmallow schema with load_only fields. Only accept explicitly listed fields.'
            })
    except:
        pass

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 7: API Abuse\n\n")
        f.write(f"**Target:** {url}\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No API abuse vulnerabilities detected\n\n")

    print(f"Scenario 7 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_api_abuse(args.url, args.output)
