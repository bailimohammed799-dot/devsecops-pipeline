# Multi-stage Dockerfile for Conduit (Flask RealWorld app)
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

# Create non-root user
RUN useradd --create-home --shell /bin/bash conduit && \
    mkdir -p /app && chown conduit:conduit /app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/conduit/.local
ENV PATH=/home/conduit/.local/bin:$PATH

# Copy application code
COPY --chown=conduit:conduit . .

# Switch to non-root user
USER conduit

# Runtime labels (set at build time via --label)
LABEL org.opencontainers.image.title="Conduit (RealWorld Flask Backend)"
LABEL org.opencontainers.image.source="https://github.com/gothinkster/flask-realworld-example-app"
LABEL org.opencontainers.image.licenses="MIT"

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/healthz')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "autoapp:app"]
