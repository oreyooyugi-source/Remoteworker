"""Application configuration for the audit app."""
from __future__ import annotations

from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    verbose_name = "Audit Log"

    def ready(self) -> None:
        from apps.audit import signals  # noqa: F401
