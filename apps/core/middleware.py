"""Core middleware components."""
from __future__ import annotations

import zoneinfo

from django.utils import timezone


class TimezoneMiddleware:
    """Activate the timezone stored on the authenticated user's profile.

    Falls back to the project default timezone for anonymous users or
    users without a configured timezone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = None
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            tzname = getattr(user, "timezone", None)
        if tzname:
            try:
                timezone.activate(zoneinfo.ZoneInfo(tzname))
            except Exception:  # noqa: BLE001 - invalid tz falls back to default
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)
