"""Application configuration for the timetracking app."""
from __future__ import annotations

from django.apps import AppConfig


class TimeTrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.timetracking"
    verbose_name = "Time Tracking"
