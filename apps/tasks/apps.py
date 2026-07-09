"""Application configuration for the tasks app."""
from __future__ import annotations

from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tasks"
    verbose_name = "Tasks"

    def ready(self) -> None:
        from apps.tasks import signals  # noqa: F401
