"""Context processor exposing notifications to every template."""
from __future__ import annotations

from apps.notifications.models import Notification


def notifications(request) -> dict:
    """Provide the unread notification count and a short recent list."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"unread_notifications": 0, "recent_notifications": []}

    qs = Notification.objects.filter(recipient=user)
    unread = qs.filter(is_read=False).count()
    recent = list(qs.select_related("actor")[:8])
    return {
        "unread_notifications": unread,
        "recent_notifications": recent,
    }
