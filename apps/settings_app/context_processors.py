"""Context processor exposing company settings to templates."""
from __future__ import annotations

from apps.settings_app.services import get_company_settings


def company_settings(request) -> dict:
    try:
        company = get_company_settings()
    except Exception:  # noqa: BLE001 - e.g. before migrations run
        company = None
    return {"company": company}
