"""Application configuration for the productivity app."""
from __future__ import annotations

from django.apps import AppConfig


class ProductivityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.productivity"
    verbose_name = "Productivity"
