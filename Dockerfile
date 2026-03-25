# ─────────────────────────────────────────────────────
# Dockerfile — AI News Dashboard
# Uses Python 3.11 — SQLAlchemy 2.x is NOT compatible
# with Python 3.14+ (Render default as of 2025).
# ─────────────────────────────────────────────────────

# Stage 1: builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies into a virtual env to keep final image clean
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────────────

# Stage 2: final image
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY . .

# Create a directory for the SQLite database that persists
RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/ai_news.db

# Expose port
EXPOSE 8000

# Health check — Render uses this to verify the service is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Start with gunicorn (production) or uvicorn (dev)
CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-"]
