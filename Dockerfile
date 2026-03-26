# ─────────────────────────────────────────────────────
# Dockerfile — AI News Dashboard (Render Ready)
# Uses Python 3.11 to avoid SQLAlchemy + Python 3.14 issues
# ─────────────────────────────────────────────────────

# Stage 1: builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────

# Stage 2: final image
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy project files
COPY . .

# Create persistent DB folder
RUN mkdir -p /data

# Default database (can override via Render env vars)
ENV DATABASE_URL=sqlite:////data/ai_news.db

# Render provides PORT dynamically
ENV PORT=8000

# Expose port
EXPOSE 8000

# ✅ Correct health check (NOT gunicorn)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:${PORT}/health')" || exit 1

# ✅ Start application (Render compatible)
CMD ["sh", "-c", "gunicorn main:app \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:${PORT} \
     --workers 2 \
     --timeout 120 \
     --access-logfile -"]
