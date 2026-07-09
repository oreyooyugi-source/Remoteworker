"""Models for screenshot monitoring."""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


def screenshot_path(instance, filename: str) -> str:
    day = timezone.now().strftime("%Y/%m/%d")
    return f"screenshots/{instance.employee_id}/{day}/{filename}"


def thumbnail_path(instance, filename: str) -> str:
    day = timezone.now().strftime("%Y/%m/%d")
    return f"screenshots/{instance.employee_id}/{day}/thumbs/{filename}"


class Screenshot(TimeStampedModel):
    class CaptureType(models.TextChoices):
        AUTOMATIC = "automatic", "Automatic"
        MANUAL = "manual", "Manual"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="screenshots",
    )
    session = models.ForeignKey(
        "monitoring.ActivitySession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="screenshots",
    )
    image = models.ImageField(upload_to=screenshot_path)
    thumbnail = models.ImageField(
        upload_to=thumbnail_path, null=True, blank=True
    )
    captured_at = models.DateTimeField(default=timezone.now, db_index=True)
    capture_type = models.CharField(
        max_length=12,
        choices=CaptureType.choices,
        default=CaptureType.AUTOMATIC,
    )

    active_application = models.CharField(max_length=200, blank=True)
    active_window_title = models.CharField(max_length=255, blank=True)
    active_website = models.CharField(max_length=255, blank=True)

    activity_level = models.PositiveSmallIntegerField(
        default=0, help_text="0-100 activity intensity at capture time."
    )
    is_blurred = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, blank=True)

    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    file_size = models.PositiveIntegerField(default=0)
    monitor_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["employee", "-captured_at"]),
            models.Index(fields=["is_flagged"]),
        ]

    def __str__(self) -> str:
        return f"Screenshot {self.employee.full_name} @ {self.captured_at:%Y-%m-%d %H:%M}"

    @property
    def thumbnail_url(self) -> str:
        if self.thumbnail:
            return self.thumbnail.url
        if self.image:
            return self.image.url
        return ""

    def flag(self, reason: str = "") -> None:
        self.is_flagged = True
        self.flag_reason = reason
        self.save(update_fields=["is_flagged", "flag_reason"])
