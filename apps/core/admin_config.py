"""Custom admin site AppConfig (kept separate to avoid AppConfig ambiguity)."""
from __future__ import annotations

from django.contrib.admin.apps import AdminConfig


class CoreAdminConfig(AdminConfig):
    """Point Django at our customised admin site."""

    default_site = "apps.core.admin.RWTAdminSite"
