#!/usr/bin/env python3
"""Scenario 10: Security Misconfiguration — default errors, stack traces, exposed consoles, missing headers."""
import argparse, requests

def test_security_misconfig(url, output_file):
    findings = []
    base = url.rstrip('/')

    # Test 1: Check security headers
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': ('DENY', 'SAMEORIGIN'),
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': None,  # Just check presence
        'Strict-Transport-Security': None,
        'Referrer-Policy': None,
        'Permissions-Policy': None,
    }

    try:
        resp = requests.get(f"{base}/api/", timeout=10)
        for header, expected in security_headers.items():
            value = resp.headers.get(header)
            if not value:
                findings.append({
                    'severity': 'Medium',
                    'description': f'Missing security header: {header}',
                    'evidence': f'Response headers: {dict(resp.headers)}',
                    'fix': f'Add {header} header in Flask after_request handler or reverse proxy.'
                })
            elif expected and value not in (expected if isinstance(expected, tuple) else (expected,)):
                findings.append({
                    'severity': 'Low',
                    'description': f'Security header {header} has suboptimal value: {value}',
                    'evidence': f'Expected one of {expected}',
                    'fix': f'Set {header}: {expected[0] if isinstance(expected, tuple) else expected}'
                })
    except:
        pass

    # Test 2: Default error pages / verbose errors
    error_triggers = [
        ('GET', '/api/nonexistent-page-404'),
        ('GET', '/api/articles/999999'),
        ('POST', '/api/users/login'),
    ]

    for method, endpoint in error_triggers:
        try:
            if method == 'GET':
                resp = requests.get(f"{base}{endpoint}", timeout=5)
            else:
                resp = requests.post(f"{base}{endpoint}",
                    json={"malformed": True}, timeout=5)

            # Check for stack traces
            for keyword in ['Traceback', 'File "', 'line ', 'Error:', 'Exception:', 'DEBUG', 'SQL:', 'sql']:
                if keyword in resp.text and resp.status_code == 500:
                    findings.append({
                        'severity': 'High',
                        'description': f'Stack trace / debug info exposed on {method} {endpoint}',
                        'evidence': f'Response contains: "{keyword}"',
                        'fix': 'Set app.debug=False. Use custom error handlers with generic messages.'
                    })
                    break

            # Check for default server headers
            server = resp.headers.get('Server', '')
            if 'Werkzeug' in server or 'Python' in server:
                findings.append({
                    'severity': 'Low',
                    'description': f'Server header reveals technology stack: {server}',
                    'evidence': f'Server: {server}',
                    'fix': 'Configure reverse proxy to remove/override Server header.'
                })
        except:
            pass

    # Test 3: Exposed admin consoles / common paths
    admin_paths = ['/admin', '/api/admin', '/swagger', '/api/docs', '/.env', '/config', '/debug']
    for path in admin_paths:
        try:
            resp = requests.get(f"{base}{path}", timeout=5, allow_redirects=False)
            if resp.status_code in (200, 301, 302) and resp.status_code != 404:
                findings.append({
                    'severity': 'Medium',
                    'description': f'Potentially exposed path: {path} (HTTP {resp.status_code})',
                    'evidence': f'Path is accessible',
                    'fix': f'Restrict access to {path} or remove it from production.'
                })
        except:
            pass

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 10: Security Misconfiguration\n\n")
        f.write(f"**Target:** {url}\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No security misconfigurations detected\n\n")

    print(f"Scenario 10 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_security_misconfig(args.url, args.output)
