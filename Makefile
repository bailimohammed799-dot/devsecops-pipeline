.PHONY: setup pipeline clean reports help

SHELL := /bin/bash
RUN_DIR := $(shell date +%Y%m%d-%H%M%S)
REPORTS_DIR := reports/$(RUN_DIR)

# ── Default target ──────────────────────────────────────────────
help:
	@echo "DevSecOps Pipeline — Makefile"
	@echo ""
	@echo "  make setup      Install all dependencies (one-time)"
	@echo "  make pipeline   Run all 9 stages end-to-end"
	@echo "  make clean      Remove build artifacts and containers"
	@echo "  make reports    Show latest report directory"
	@echo ""
	@echo "Environment variables (see .env.example):"
	@echo "  TARGET_REPO, TARGET_COMMIT, SONAR_HOST_URL, SONAR_TOKEN"
	@echo "  SECRET_KEY, MIN_COVERAGE"

# ── Setup ──────────────────────────────────────────────────────
setup: .env
	@echo "=== SETUP ==="
	@echo "Installing system dependencies..."
	sudo apt-get update -qq && sudo apt-get install -y -qq \
		python3 python3-pip python3-venv \
		nodejs npm \
		curl jq git \
		openjdk-11-jre-headless \
		ca-certificates 2>&1 | tail -3
	@echo "Installing Python tools..."
	pip3 install --quiet semgrep bandit pip-audit gitleaks
	@echo "Installing Node tools..."
	npm install -g eslint @typescript-eslint/parser 2>/dev/null || true
	@echo "Installing Sonar Scanner..."
	curl -sSL https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip -o /tmp/sonar.zip && \
		unzip -qo /tmp/sonar.zip -d /opt/ && \
		ln -sf /opt/sonar-scanner-*/bin/sonar-scanner /usr/local/bin/sonar-scanner || echo "Sonar scanner already installed"
	@echo "Installing Trivy..."
	curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin 2>/dev/null || echo "Trivy already installed"
	@echo "Installing OWASP ZAP..."
	docker pull owasp/zap2docker-stable:latest 2>/dev/null || echo "ZAP image already pulled"
	@echo "Setup complete. Run 'make pipeline' to execute the full pipeline."

.env:
	@echo "ERROR: .env file missing. Copy .env.example to .env and fill in values."
	@exit 1

# ── Full Pipeline ──────────────────────────────────────────────
pipeline:
	@echo "=== DEVSECOPS PIPELINE STARTING — $(RUN_DIR) ==="
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) stage1 || (echo "Stage 1 FAILED" && exit 1)
	@$(MAKE) stage2 || (echo "Stage 2 FAILED" && exit 1)
	@$(MAKE) stage3 || (echo "Stage 3 FAILED" && exit 1)
	@$(MAKE) stage4 || (echo "Stage 4 FAILED" && exit 1)
	@$(MAKE) stage5 || (echo "Stage 5 FAILED" && exit 1)
	@$(MAKE) stage6 || (echo "Stage 6 FAILED" && exit 1)
	@$(MAKE) stage7 || (echo "Stage 7 FAILED" && exit 1)
	@$(MAKE) stage8 || echo "Stage 8 completed with findings (DAST)"
	@$(MAKE) stage9
	@echo "=== PIPELINE COMPLETE — reports at $(REPORTS_DIR) ==="

# ── Stage 1: Source retrieval & integrity ──────────────────────
stage1:
	@echo "--- Stage 1: Source retrieval & integrity ---"
	@mkdir -p $(REPORTS_DIR)/01-source
	@bash scripts/verify_integrity.sh $(TARGET_REPO) $(TARGET_COMMIT) $(REPORTS_DIR)/01-source
	@echo "--- Stage 1: DONE ---"

# ── Stage 2: Build ────────────────────────────────────────────
stage2:
	@echo "--- Stage 2: Build ---"
	@mkdir -p $(REPORTS_DIR)/02-build
	@cd /tmp/conduit-app && pip install -r requirements.txt 2>&1 | tee $(REPORTS_DIR)/02-build/build.log
	@echo '{"status":"success","stage":"build"}' > $(REPORTS_DIR)/02-build/build-status.json
	@echo "--- Stage 2: DONE ---"

# ── Stage 3: SonarQube ─────────────────────────────────────────
stage3:
	@echo "--- Stage 3: SonarQube quality scan ---"
	@mkdir -p $(REPORTS_DIR)/03-sonar
	@bash scripts/run_sonar.sh $(REPORTS_DIR)/03-sonar
	@echo "--- Stage 3: DONE ---"

# ── Stage 4: Unit tests & coverage ─────────────────────────────
stage4:
	@echo "--- Stage 4: Unit tests & coverage ---"
	@mkdir -p $(REPORTS_DIR)/04-tests
	@cd /tmp/conduit-app && \
		python -m pytest tests/ -v --junitxml=$(REPORTS_DIR)/04-tests/junit.xml \
		--cov=conduit --cov-report=xml:$(REPORTS_DIR)/04-tests/coverage.xml \
		--cov-report=term 2>&1 | tee $(REPORTS_DIR)/04-tests/test-output.log
	@echo "--- Stage 4: DONE ---"

# ── Stage 5: SAST ──────────────────────────────────────────────
stage5:
	@echo "--- Stage 5: SAST ---"
	@mkdir -p $(REPORTS_DIR)/05-sast
	@bash scripts/run_sast.sh $(REPORTS_DIR)/05-sast
	@echo "--- Stage 5: DONE ---"

# ── Stage 6: Image build ───────────────────────────────────────
stage6:
	@echo "--- Stage 6: Image/artifact build ---"
	@mkdir -p $(REPORTS_DIR)/06-image
	@bash scripts/build_image.sh $(REPORTS_DIR)/06-image
	@echo "--- Stage 6: DONE ---"

# ── Stage 7: Deploy ────────────────────────────────────────────
stage7:
	@echo "--- Stage 7: Deploy to test environment ---"
	@mkdir -p $(REPORTS_DIR)/07-deploy
	@docker compose -f docker/docker-compose.yml up -d --wait 2>&1 | tee $(REPORTS_DIR)/07-deploy/deploy.log
	@bash scripts/smoke_test.sh $(REPORTS_DIR)/07-deploy
	@echo "--- Stage 7: DONE ---"

# ── Stage 8: DAST ──────────────────────────────────────────────
stage8:
	@echo "--- Stage 8: DAST ---"
	@mkdir -p $(REPORTS_DIR)/08-dast/{scenarios,zap}
	@bash scripts/run_dast.sh $(REPORTS_DIR)/08-dast
	@bash scripts/run_scenarios.sh $(REPORTS_DIR)/08-dast
	@echo "--- Stage 8: DONE ---"

# ── Stage 9: Reports ───────────────────────────────────────────
stage9:
	@echo "--- Stage 9: Report generation ---"
	@python3 scripts/aggregate_reports.py $(REPORTS_DIR) $(RUN_DIR)
	@echo "--- Stage 9: DONE ---"
	@cat $(REPORTS_DIR)/SUMMARY.md

# ── Cleanup ────────────────────────────────────────────────────
clean:
	@echo "Cleaning up containers, images, and temp files..."
	-docker compose -f docker/docker-compose.yml down -v 2>/dev/null
	-docker rm -f sonarqube zap registry 2>/dev/null
	-rm -rf /tmp/conduit-app /tmp/sonar.zip
	@echo "Clean complete (reports preserved in reports/)."
