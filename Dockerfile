# ─── Build Stage ──────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .

# ─── Runtime Stage ────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="Mohammed Anirudh"
LABEL description="NETAI: AI-Powered Kubernetes Chatbot for Network Diagnostics"
LABEL org.opencontainers.image.source="https://github.com/Mohammed-Anirudh/NETAI-LLM-Integration-Chatbot"

# Non-root user for security
RUN groupadd -r netai && useradd -r -g netai -d /app -s /sbin/nologin netai

WORKDIR /app

# Copy installed packages and application
COPY --from=builder /install /usr/local
COPY src/ src/
COPY static/ static/

# Set ownership
RUN chown -R netai:netai /app

USER netai

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()"

EXPOSE 8000

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

CMD ["python", "-m", "uvicorn", "netai_chatbot.main:app", "--host", "0.0.0.0", "--port", "8000"]
