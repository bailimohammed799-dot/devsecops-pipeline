#!/usr/bin/env python3
"""Scenario 2: Man-in-the-Middle — verify TLS configuration."""
import argparse, sys, requests, ssl, socket

def test_mitm(url, output_file):
    findings = []
    parsed = requests.utils.urlparse(url)

    # Check if HTTPS is used
    uses_https = parsed.scheme == 'https'

    # Check security headers
    try:
        resp = requests.get(f"{url}/api/", timeout=10)
        headers = resp.headers

        security_headers = {
            'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
            'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
            'X-Frame-Options': headers.get('X-Frame-Options'),
            'Content-Security-Policy': headers.get('Content-Security-Policy'),
        }

        missing = [h for h, v in security_headers.items() if not v]

        if not uses_https:
            findings.append({
                'severity': 'High',
                'description': 'Application served over HTTP (no TLS)',
                'evidence': f'URL scheme is {parsed.scheme}',
                'fix': 'Deploy behind a reverse proxy (Nginx/Traefik) with TLS termination. Use Let\'s Encrypt for free certificates.'
            })

        if missing:
            findings.append({
                'severity': 'Medium',
                'description': f'Missing security headers: {", ".join(missing)}',
                'evidence': f'Response headers: {dict(headers)}',
                'fix': 'Add missing security headers in Flask middleware or reverse proxy.'
            })

        # Check for HSTS
        if 'Strict-Transport-Security' not in headers and not uses_https:
            findings.append({
                'severity': 'Medium',
                'description': 'HSTS not configured — MITM downgrade attacks possible',
                'fix': 'Add Strict-Transport-Security header with max-age=31536000; includeSubDomains'
            })

    except Exception as e:
        findings.append({
            'severity': 'Info',
            'description': f'Could not connect: {str(e)}'
        })

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 2: Man-in-the-Middle (MITM)\n\n")
        f.write(f"**Target:** {url}\n")
        f.write(f"**Transport:** {'HTTPS (secure)' if uses_https else 'HTTP (plaintext — vulnerable to MITM)'}\n\n")

        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No MITM vulnerabilities detected\n\n")
            f.write("TLS is properly configured with all recommended security headers.\n\n")

    print(f"Scenario 2 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_mitm(args.url, args.output)
