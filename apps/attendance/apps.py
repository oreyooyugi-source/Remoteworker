"""Application configuration for the attendance app."""
from __future__ import annotations

from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.attendance"
    verbose_name = "Attendance"

    def ready(self) -> None:
        from apps.attendance import signals  # noqa: F401
