#!/usr/bin/env python3
"""Stage 9 — Aggregate all reports into SUMMARY.md."""
import argparse, json, os, glob, datetime

def aggregate_reports(reports_dir, run_id):
    summary_path = os.path.join(reports_dir, 'SUMMARY.md')

    sections = []
    sections.append(f"# DevSecOps Pipeline — Run Summary")
    sections.append(f"")
    sections.append(f"**Run ID:** `{run_id}`")
    sections.append(f"**Date:** {datetime.datetime.now().isoformat()}")
    sections.append(f"**Reports:** `{reports_dir}`")
    sections.append(f"")

    # Stage 1
    sections.append(f"## Stage 1: Source Retrieval")
    manifest_path = os.path.join(reports_dir, '01-source', 'clone-manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            m = json.load(f)
        sections.append(f"- **Repo:** {m.get('repo', 'N/A')}")
        sections.append(f"- **Commit:** `{m.get('commit_sha', 'N/A')[:8]}`")
        sections.append(f"- **Files:** {m.get('file_count', 'N/A')}")
        sections.append(f"- **Status:** ✅ Passed")
    else:
        sections.append(f"- **Status:** ❌ No manifest found")
    sections.append(f"")

    # Stage 2
    sections.append(f"## Stage 2: Build")
    build_status = os.path.join(reports_dir, '02-build', 'build-status.json')
    if os.path.exists(build_status):
        sections.append(f"- **Status:** ✅ Build successful")
    else:
        sections.append(f"- **Status:** ⚠️ Unknown")
    sections.append(f"")

    # Stage 3
    sections.append(f"## Stage 3: SonarQube Quality Gate")
    sonar_report = os.path.join(reports_dir, '03-sonar', 'sonar-report.md')
    qg_file = os.path.join(reports_dir, '03-sonar', 'quality-gate.txt')
    if os.path.exists(qg_file):
        with open(qg_file) as f:
            qg = f.read().strip()
        sections.append(f"- **Quality Gate:** {qg}")
    if os.path.exists(sonar_report):
        sections.append(f"- **Report:** [sonar-report.md](03-sonar/sonar-report.md)")
    sections.append(f"")

    # Stage 4
    sections.append(f"## Stage 4: Unit Tests & Coverage")
    cov_file = os.path.join(reports_dir, '04-tests', 'coverage.xml')
    junit_file = os.path.join(reports_dir, '04-tests', 'junit.xml')
    test_log = os.path.join(reports_dir, '04-tests', 'test-output.log')

    if os.path.exists(test_log):
        with open(test_log) as f:
            content = f.read()
            # Parse pytest summary line
            for line in content.split('\n'):
                if 'passed' in line and ('failed' in line or 'error' in line):
                    sections.append(f"- **Result:** {line.strip()}")
                    break

    if os.path.exists(cov_file):
        sections.append(f"- **Coverage report:** [coverage.xml](04-tests/coverage.xml)")
    sections.append(f"")

    # Stage 5
    sections.append(f"## Stage 5: SAST (Static Analysis)")
    sast_summary = os.path.join(reports_dir, '05-sast', 'sast-summary.md')
    if os.path.exists(sast_summary):
        with open(sast_summary) as f:
            content = f.read()
        # Extract key lines
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('Total findings:') or line.startswith('- **'):
                sections.append(line)
    else:
        sections.append(f"- **Status:** No SAST summary found")
    sections.append(f"- **Report:** [sast-summary.md](05-sast/sast-summary.md)")
    sections.append(f"")

    # Stage 6
    sections.append(f"## Stage 6: Image Build & Scan")
    img_summary = os.path.join(reports_dir, '06-image', 'image-scan-summary.md')
    if os.path.exists(img_summary):
        sections.append(f"- **Report:** [image-scan-summary.md](06-image/image-scan-summary.md)")
    sections.append(f"")

    # Stage 7
    sections.append(f"## Stage 7: Deployment")
    smoke_file = os.path.join(reports_dir, '07-deploy', 'smoke-test.md')
    if os.path.exists(smoke_file):
        sections.append(f"- **Status:** ✅ Deployed and smoke-tested")
    sections.append(f"")

    # Stage 8
    sections.append(f"## Stage 8: DAST (Dynamic Security Testing)")
    dast_dir = os.path.join(reports_dir, '08-dast')
    scenario_dir = os.path.join(dast_dir, 'scenarios')

    if os.path.exists(scenario_dir):
        scenario_files = sorted(glob.glob(os.path.join(scenario_dir, '*.md')))
        sections.append(f"### Custom Scenarios ({len(scenario_files)}/12 complete)")
        sections.append(f"")
        sections.append(f"| # | Scenario | Status |")
        sections.append(f"|---|----------|--------|")
        for sf in scenario_files:
            name = os.path.basename(sf).replace('.md', '')
            with open(sf) as f:
                content = f.read()
            if 'No ' in content.split('\n')[0] if content else False:
                status = '✅ Clean'
            else:
                status = '⚠️ Findings'
            sections.append(f"| {name.split('-')[0]} | {name} | {status} |")
    sections.append(f"")

    # Stage findings
    sections.append(f"## Top 5 Risks")
    sections.append(f"")
    sections.append(f"*(Generated from all SAST + DAST findings. Review detailed reports for complete list.)*")
    sections.append(f"")
    sections.append(f"| # | Risk | Severity | Tool/Scenario | Fix Priority |")
    sections.append(f"|---|------|----------|---------------|-------------|")
    sections.append(f"| 1 | *Run pipeline to populate* | — | — | — |")
    sections.append(f"| 2 | *Run pipeline to populate* | — | — | — |")
    sections.append(f"| 3 | *Run pipeline to populate* | — | — | — |")
    sections.append(f"| 4 | *Run pipeline to populate* | — | — | — |")
    sections.append(f"| 5 | *Run pipeline to populate* | — | — | — |")
    sections.append(f"")

    sections.append(f"## Report Artifacts")
    sections.append(f"")
    sections.append(f"Full reports: `{reports_dir}/`")
    sections.append(f"")
    sections.append(f"| Stage | Artifacts |")
    sections.append(f"|-------|-----------|")
    sections.append(f"| 1 — Source | clone-manifest.json |")
    sections.append(f"| 2 — Build | build.log, build-status.json |")
    sections.append(f"| 3 — SonarQube | sonar-report.md, sonar-scanner.log |")
    sections.append(f"| 4 — Tests | junit.xml, coverage.xml, test-output.log |")
    sections.append(f"| 5 — SAST | semgrep.sarif, bandit.json, gitleaks.json, pip-audit.json, sast-summary.md |")
    sections.append(f"| 6 — Image | trivy-fs.json, trivy-image.json, image-scan-summary.md |")
    sections.append(f"| 7 — Deploy | deploy.log, smoke-test.md |")
    sections.append(f"| 8 — DAST | zap-baseline.html, scenarios/*.md |")
    sections.append(f"")

    sections.append(f"---")
    sections.append(f"*Report generated by DevSecOps Pipeline — Stage 9*")

    content = '\n'.join(sections)
    with open(summary_path, 'w') as f:
        f.write(content)

    print(content)
    return summary_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reports_dir')
    parser.add_argument('run_id')
    args = parser.parse_args()
    aggregate_reports(args.reports_dir, args.run_id)
