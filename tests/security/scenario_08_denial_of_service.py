#!/usr/bin/env python3
"""Scenario 8: Denial of Service — resource exhaustion payloads (throttled, test env only)."""
import argparse, requests, time, threading

def test_dos(url, output_file):
    findings = []
    base = url.rstrip('/')

    # Test 1: Large payload (body size)
    large_payloads = [
        {"user": {"username": "a" * 10000, "email": "large@test.com", "password": "Test123!"}},
        {"article": {"title": "x" * 50000, "description": "x" * 50000, "body": "x" * 100000, "tagList": ["x"] * 1000}},
    ]

    for i, payload in enumerate(large_payloads):
        try:
            start = time.time()
            resp = requests.post(f"{base}/api/users" if "user" in str(payload) else f"{base}/api/articles",
                json=payload, timeout=30)
            elapsed = time.time() - start
            if elapsed > 10:
                findings.append({
                    'severity': 'Medium',
                    'description': f'Large payload #{i} caused slow response ({elapsed:.1f}s)',
                    'evidence': f'Response time: {elapsed:.1f}s, HTTP {resp.status_code}',
                    'fix': 'Implement request body size limits. Use Flask app.config[\"MAX_CONTENT_LENGTH\"].'
                })
        except requests.exceptions.Timeout:
            findings.append({
                'severity': 'High',
                'description': f'Large payload #{i} caused request timeout (DoS possible)',
                'evidence': 'Request timed out after 30 seconds',
                'fix': 'Add request size limits and timeout middleware. Implement connection rate limiting.'
            })
        except:
            pass

    # Test 2: Concurrent connections (small-scale, throttled)
    concurrent_results = []
    def make_request():
        try:
            resp = requests.get(f"{base}/api/articles", timeout=10)
            concurrent_results.append(resp.status_code)
        except:
            concurrent_results.append('timeout')

    threads = []
    for _ in range(10):  # Only 10 concurrent — test env, not a real DoS
        t = threading.Thread(target=make_request)
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=15)

    errors = sum(1 for r in concurrent_results if r == 'timeout' or (isinstance(r, int) and r >= 500))
    if errors > 2:
        findings.append({
            'severity': 'Medium',
            'description': f'Application degraded under moderate concurrency ({errors}/{len(concurrent_results)} errors)',
            'evidence': f'Results: {concurrent_results}',
            'fix': 'Add connection pooling, increase gunicorn workers, add request queuing.'
        })

    # Test 3: Slowloris-style (slow headers)
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        host = base.replace('http://', '').replace('https://', '').split(':')[0]
        port = int(base.split(':')[-1]) if ':' in base.replace('http://', '').replace('https://', '') else 80
        sock.connect((host, port))
        sock.send(b"GET /api/articles HTTP/1.1\r\nHost: " + host.encode() + b"\r\n")
        time.sleep(8)  # Hold connection open slowly
        sock.send(b"X-Slow: slow\r\n\r\n")
        data = sock.recv(4096)
        sock.close()
        # If we got a response, the server didn't timeout the slow connection
        if data:
            findings.append({
                'severity': 'Low',
                'description': 'Server accepted slow HTTP connection (potential slowloris target)',
                'evidence': 'Server waited 8+ seconds for complete headers',
                'fix': 'Configure reverse proxy (Nginx) with client_header_timeout and client_body_timeout.'
            })
    except:
        pass

    with open(output_file, 'w') as f:
        f.write(f"# Scenario 8: Denial of Service (DoS)\n\n")
        f.write(f"**Target:** {url}\n")
        f.write(f"**Note:** Tests are throttled for safety — this is a test environment.\n\n")
        if findings:
            f.write(f"## Findings: {len(findings)} issues found\n\n")
            for i, fg in enumerate(findings, 1):
                f.write(f"### Finding {i}: {fg.get('severity', 'Info')} — {fg['description']}\n\n")
                f.write(f"- **Evidence:** {fg.get('evidence', 'N/A')}\n")
                f.write(f"- **Fix:** {fg.get('fix', 'N/A')}\n\n")
        else:
            f.write("## Result: No DoS vulnerabilities detected\n\n")

    print(f"Scenario 8 complete — {len(findings)} findings")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    test_dos(args.url, args.output)
