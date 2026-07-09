"""Service helpers for company settings."""
from __future__ import annotations

from django.core.cache import cache

CACHE_KEY = "company_settings"
CACHE_TTL = 300


def get_company_settings():
    """Return the singleton :class:`CompanySettings`, cached briefly."""
    from apps.settings_app.models import CompanySettings

    settings_obj = cache.get(CACHE_KEY)
    if settings_obj is None:
        settings_obj = CompanySettings.load()
        cache.set(CACHE_KEY, settings_obj, CACHE_TTL)
    return settings_obj


def invalidate_company_settings() -> None:
    cache.delete(CACHE_KEY)
