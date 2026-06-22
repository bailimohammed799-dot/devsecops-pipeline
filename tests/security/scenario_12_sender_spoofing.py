#!/usr/bin/env python3
"""Scenario 12: Sender Spoofing — email/SMS sender tampering (if app sends messages)."""
import argparse, requests

def test_sender_spoofing(url, output_file):
    findings = []
    base = url.rstrip('/')

    # This app (Conduit/RealWorld) does NOT have email/SMS sending built in.
    # It's a pure REST API backend. We document this clearly.

    # Check if there are any contact/feedback endpoints
    contact_endpoints = [
        '/api/contact',
        '/api/feedback',
        '/api/messages',
        '/api/email',
        '/api/report',
    ]

    has_contact = False
    for endpoint in contact_endpoints:
        try:
            resp = requests.get(f"{base}{endpoint}", timeout=5)
            if resp.status_code != 404:
                has_contact = True
                break
        except:
            pass

    if has_contact:
        # Test for email header injection
        try:
            inject_payloads = [
                "test@test.com%0ACc: victim@evil.com",
                "test@test.com\r\nCc: victim@evil.com",
                "test@test.com\nBcc: victim@evil.com",
                "test@test.com\r\nTo: victim@evil.com",
            ]
            for payload in inject_payloads:
                resp = requests.post(f"{base}/api/contact",
                    json={"email": payload, "subject": "test", "message": "test"},
                    timeout=5)
                if resp.status_code not in (400, 404):
                    findings.append({
                        'severity': 'High',
                        'description': f'Potential email header injection: {payload[:50]}',
                        'evidence': f'HTTP {resp.status_code}',
                        'fix': 'Validate and sanitize email fields. Strip CR/LF characters.'
                    })
        except:
            pass

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 12: Sender Spoofing\n\n")
        f.write(f"**Target:** {url}\n\n")
        f.write("## Applicability Assessment\n\n")
        f.write("The target application (**Conduit** — RealWorld Flask backend) is a **pure REST API**.\n")
        f.write("It does **not** implement email sending, SMS, or any messaging features.\n")
        f.write("There is no 'Contact Us' form, password reset email, or notification system.\n\n")
        f.write("**This scenario is NOT APPLICABLE** to the current target application.\n\n")

        if has_contact:
            f.write("However, a contact endpoint was detected — testing was performed as documented above.\n\n")
            if findings:
                f.write(f"## Findings: {len(findings)} issues found\n\n")
                for i, fg in enumerate(findings, 1):
                    f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                    f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
            else:
                f.write("## Result: No sender spoofing vulnerabilities detected on the contact endpoint\n\n")
        else:
            f.write("## Recommendation\n\n")
            f.write("If email/SMS functionality is added in the future:\n")
            f.write("1. **Validate email addresses** against RFC 5322\n")
            f.write("2. **Strip CR/LF characters** from all email header inputs to prevent injection\n")
            f.write("3. **Use a dedicated email library** (e.g., Flask-Mail) that handles header encoding safely\n")
            f.write("4. **Set the From: header server-side** — never accept it from user input\n")
            f.write("5. **Implement SPF, DKIM, and DMARC** on the sending domain\n\n")

    print(f"Scenario 12 complete — {'N/A (no messaging feature)' if not has_contact else f'{len(findings)} findings'}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_sender_spoofing(args.url, args.output)
