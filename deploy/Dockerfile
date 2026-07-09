# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Remote Worker Tracker System — production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# System dependencies (build tools for wheels, then trimmed).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt gunicorn

# Copy the application source.
COPY . .

# Ensure shell scripts are executable inside the image.
RUN chmod +x deploy/*.sh

# Collect static assets into STATIC_ROOT (served by WhiteNoise).
RUN SECRET_KEY=build-time-key ALLOWED_HOSTS=* \
    python manage.py collectstatic --noinput

# Create a non-root user and prepare writable directories.
RUN useradd --create-home appuser \
    && mkdir -p /app/media /app/logs /app/backups \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Entrypoint runs migrations then launches Gunicorn.
ENTRYPOINT ["/app/deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-c", "deploy/gunicorn.conf.py"]
