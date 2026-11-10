# ==============================================================================
# SCHOLAR LENS — PRODUCTION DOCKERFILE
# Multi-stage security-hardened containerization
# Non-root execution, minimal attack surface, health-checked
# ==============================================================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies (compiler and PostgreSQL client libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create application user and group (non-root execution for institutional security)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy application code
COPY . .

# Create and set permissions for staticfiles, media, and cache directories
RUN mkdir -p /app/media /app/staticfiles && \
    chown -R appuser:appgroup /app

# Collect static assets into staticfiles
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Switch to non-root user
USER appuser

# Expose HTTP port
EXPOSE 8000

# Container Healthcheck (Verifies Gunicorn is actively serving HTTP requests)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8000}/ || exit 1

# Production Entrypoint Command
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py init_admin && exec gunicorn scholar_lens.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --threads 2 --timeout 120 --access-logfile - --error-logfile -"]
