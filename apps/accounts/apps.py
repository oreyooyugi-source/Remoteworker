"""Application configuration for the accounts app."""
from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Accounts & Authentication"

    def ready(self) -> None:
        from apps.accounts import signals  # noqa: F401
