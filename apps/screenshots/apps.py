"""Application configuration for the screenshots app."""
from __future__ import annotations

from django.apps import AppConfig


class ScreenshotsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.screenshots"
    verbose_name = "Screenshots"
