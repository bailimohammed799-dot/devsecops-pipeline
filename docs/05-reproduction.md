# 05 — Reproduction Guide

Step-by-step instructions to reproduce the full pipeline from a fresh Ubuntu 22.04 machine.

## Prerequisites

- Ubuntu 22.04 LTS (fresh install)
- At least 8 GB RAM (SonarQube needs ~3 GB)
- 20 GB free disk space
- Internet connection

## Step 1: Install System Dependencies

```bash
# Update packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker  # or log out and back in

# Install other dependencies
sudo apt-get install -y \
    git make curl jq \
    python3 python3-pip python3-venv \
    openjdk-11-jre-headless
```

## Step 2: Clone the Pipeline Repository

```bash
git clone https://github.com/USER/devsecops-pipeline.git
cd devsecops-pipeline
```

## Step 3: Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your values
nano .env
# Required variables:
#   SONAR_TOKEN=your-sonarqube-token
#   SECRET_KEY=your-random-secret-key
```

## Step 4: Run Setup

```bash
make setup
```

This installs:
- Python tools: semgrep, bandit, pip-audit, pytest
- Node.js + npm (for npm audit on optional JS deps)
- Sonar Scanner CLI
- Trivy vulnerability scanner
- OWASP ZAP Docker image

**Expected runtime:** ~10 minutes (mostly Docker pulls)

## Step 5: Run the Pipeline

```bash
make pipeline
```

**Expected runtime:** ~15-20 minutes total

### What happens:
1. **Stage 1 (~30s):** Clones `gothinkster/flask-realworld-example-app` at pinned commit
2. **Stage 2 (~2m):** Installs Python dependencies
3. **Stage 3 (~3m):** Starts SonarQube, runs analysis, checks quality gate
4. **Stage 4 (~1m):** Runs pytest with coverage
5. **Stage 5 (~2m):** Runs Semgrep, Bandit, Gitleaks, pip-audit
6. **Stage 6 (~3m):** Builds Docker image, scans with Trivy
7. **Stage 7 (~1m):** Deploys via docker compose, smoke tests
8. **Stage 8 (~5m):** Runs ZAP + 12 custom DAST scenarios
9. **Stage 9 (~5s):** Generates SUMMARY.md

## Step 6: View Results

```bash
# Find the latest run
ls reports/

# Read the summary
cat reports/$(ls -1t reports/ | head -1)/SUMMARY.md

# Browse detailed reports
ls -R reports/$(ls -1t reports/ | head -1)/

# Open SonarQube dashboard
# http://localhost:9000/dashboard?id=conduit
```

## Troubleshooting

### SonarQube fails to start
```bash
# Check Docker memory
docker stats --no-stream

# SonarQube needs ≥ 2 GB RAM. Increase Docker Desktop memory limit.
# Check logs:
docker logs sonarqube
```

### Tests fail with "could not connect to database"
```bash
# Ensure PostgreSQL is running
docker ps | grep postgres

# Check database URL
echo $DATABASE_URL
```

### "permission denied" on Docker commands
```bash
# Ensure user is in docker group
groups | grep docker
# If not:
sudo usermod -aG docker $USER
# Log out and back in
```

### Semgrep not found
```bash
# Install manually
pip3 install --user semgrep
export PATH=$PATH:$HOME/.local/bin
```

### Clean up everything
```bash
make clean
# This stops all containers but preserves reports/
docker system prune -a  # Optional: remove all Docker images/cache
```
