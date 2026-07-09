"""Application configuration for the employees app."""
from __future__ import annotations

from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.employees"
    verbose_name = "Employees"

    def ready(self) -> None:
        from apps.employees import signals  # noqa: F401
