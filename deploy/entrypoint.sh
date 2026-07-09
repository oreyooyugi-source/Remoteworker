#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Container entrypoint: prepare the app, then exec the given command.
# ---------------------------------------------------------------------------
set -euo pipefail

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

# Optionally create a superuser from environment variables.
if [[ -n "${DJANGO_SUPERUSER_EMAIL:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
    echo "==> Ensuring superuser ${DJANGO_SUPERUSER_EMAIL} exists"
    python manage.py createsuperuser --noinput \
        --email "${DJANGO_SUPERUSER_EMAIL}" \
        --username "${DJANGO_SUPERUSER_USERNAME:-admin}" || true
fi

echo "==> Starting: $*"
exec "$@"
