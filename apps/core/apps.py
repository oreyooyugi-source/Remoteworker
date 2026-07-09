"""Application configuration for the core app."""
from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the shared core application."""

    default = True
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self) -> None:  # noqa: D401
        """Import signal handlers when the app registry is ready."""
        # Importing here avoids AppRegistryNotReady errors.
        from apps.core import signals  # noqa: F401
