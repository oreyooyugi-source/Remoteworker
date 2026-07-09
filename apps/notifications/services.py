"""Notification service functions used across the project."""
from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from apps.notifications.models import (
    Notification,
    NotificationPreference,
    NotificationType,
)


def get_preferences(user) -> NotificationPreference:
    prefs, _created = NotificationPreference.objects.get_or_create(user=user)
    return prefs


_CATEGORY_PREF_MAP = {
    NotificationType.ATTENDANCE: "notify_attendance",
    NotificationType.TASK: "notify_tasks",
    NotificationType.PROJECT: "notify_projects",
    NotificationType.APPROVAL: "notify_approvals",
    NotificationType.LEAVE: "notify_approvals",
    NotificationType.PAYROLL: "notify_payroll",
    NotificationType.MENTION: "notify_mentions",
    NotificationType.ANNOUNCEMENT: "notify_announcements",
}


def notify(
    recipient,
    title: str,
    message: str = "",
    *,
    notification_type: str = NotificationType.SYSTEM,
    priority: str = "medium",
    icon: str = "fa-bell",
    url: str = "",
    actor=None,
    send_email: bool | None = None,
) -> Notification | None:
    """Create a notification, honouring the recipient's preferences."""
    prefs = get_preferences(recipient)

    category_field = _CATEGORY_PREF_MAP.get(notification_type)
    if category_field and not getattr(prefs, category_field, True):
        return None
    if not prefs.in_app_enabled:
        return None

    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        priority=priority,
        title=title[:160],
        message=message,
        icon=icon,
        url=url,
    )

    should_email = send_email if send_email is not None else prefs.email_enabled
    if should_email and prefs.digest_frequency == "instant":
        _send_email(recipient, title, message)
        notification.emailed = True
        notification.save(update_fields=["emailed"])

    return notification


def _send_email(recipient, subject: str, message: str) -> None:
    try:
        send_mail(
            subject=f"[{settings.RWT['APP_SHORT_NAME']}] {subject}",
            message=message or subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,
        )
    except Exception:  # noqa: BLE001
        pass


def notify_many(recipients, title: str, message: str = "", **kwargs) -> int:
    """Send the same notification to many recipients. Returns the count."""
    count = 0
    with transaction.atomic():
        for recipient in recipients:
            if notify(recipient, title, message, **kwargs):
                count += 1
    return count


def notify_role(role: str, title: str, message: str = "", **kwargs) -> int:
    """Notify every active user holding ``role``."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    recipients = User.objects.filter(role=role, is_active=True)
    return notify_many(recipients, title, message, **kwargs)


def mark_all_read(user) -> int:
    from django.utils import timezone

    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def unread_count(user) -> int:
    return Notification.objects.filter(recipient=user, is_read=False).count()
