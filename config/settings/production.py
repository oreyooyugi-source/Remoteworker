"""Production settings for the Remote Worker Tracker System."""
from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import env

# ---------------------------------------------------------------------------
# Debugging must be disabled in production
# ---------------------------------------------------------------------------
DEBUG = False

# ALLOWED_HOSTS must be supplied via the environment.
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# HTTPS / transport security
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Static files — compressed & hashed manifest storage served by WhiteNoise
# ---------------------------------------------------------------------------
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Email (real SMTP backend)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

# ---------------------------------------------------------------------------
# Admins receive error emails
# ---------------------------------------------------------------------------
ADMINS = [("RWT Operations", env("ADMIN_EMAIL", default="ops@rwt.local"))]
MANAGERS = ADMINS
