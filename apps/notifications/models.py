"""Models for notifications, preferences and announcements."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.constants import Priority
from apps.core.models import TimeStampedModel


class NotificationType(models.TextChoices):
    SYSTEM = "system", "System"
    ATTENDANCE = "attendance", "Attendance"
    TASK = "task", "Task"
    PROJECT = "project", "Project"
    APPROVAL = "approval", "Approval"
    LEAVE = "leave", "Leave"
    PAYROLL = "payroll", "Payroll"
    MENTION = "mention", "Mention"
    ALERT = "alert", "Alert"
    ANNOUNCEMENT = "announcement", "Announcement"


class Notification(TimeStampedModel):
    """A single in-app notification addressed to one user."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    icon = models.CharField(max_length=40, default="fa-bell")
    url = models.CharField(max_length=255, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    emailed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self) -> str:
        return f"{self.title} -> {self.recipient}"

    def mark_read(self) -> None:
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    @property
    def color(self) -> str:
        from apps.core.constants import STATUS_COLORS

        return STATUS_COLORS.get(self.priority, "primary")

    def get_absolute_url(self) -> str:
        return self.url or reverse("notifications:list")


class NotificationPreference(TimeStampedModel):
    """Per-user delivery preferences by channel and category."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    browser_enabled = models.BooleanField(default=True)

    notify_attendance = models.BooleanField(default=True)
    notify_tasks = models.BooleanField(default=True)
    notify_projects = models.BooleanField(default=True)
    notify_approvals = models.BooleanField(default=True)
    notify_payroll = models.BooleanField(default=True)
    notify_mentions = models.BooleanField(default=True)
    notify_announcements = models.BooleanField(default=True)

    digest_frequency = models.CharField(
        max_length=10,
        choices=[
            ("instant", "Instant"),
            ("daily", "Daily digest"),
            ("weekly", "Weekly digest"),
            ("off", "Off"),
        ],
        default="instant",
    )

    class Meta:
        verbose_name = "Notification preference"
        verbose_name_plural = "Notification preferences"

    def __str__(self) -> str:
        return f"Preferences — {self.user}"


class Announcement(TimeStampedModel):
    """A company-wide or department-scoped broadcast message."""

    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements",
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    department = models.ForeignKey(
        "employees.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcements",
        help_text="Leave blank to broadcast to the whole company.",
    )
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-pinned", "-published_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_active(self) -> bool:
        if not self.is_published:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True
