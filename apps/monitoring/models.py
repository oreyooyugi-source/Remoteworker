"""Models for activity monitoring and device telemetry."""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class ActivitySession(TimeStampedModel):
    """A continuous monitored work session on a device."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="activity_sessions",
    )
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    active_seconds = models.PositiveIntegerField(default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    break_seconds = models.PositiveIntegerField(default=0)
    meeting_seconds = models.PositiveIntegerField(default=0)

    keyboard_events = models.PositiveIntegerField(default=0)
    mouse_events = models.PositiveIntegerField(default=0)
    mouse_distance = models.PositiveIntegerField(default=0)

    # Environment
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    hostname = models.CharField(max_length=120, blank=True)
    operating_system = models.CharField(max_length=80, blank=True)
    browser = models.CharField(max_length=80, blank=True)
    device_name = models.CharField(max_length=120, blank=True)
    is_vpn = models.BooleanField(default=False)
    monitor_count = models.PositiveSmallIntegerField(default=1)
    timezone_name = models.CharField(max_length=64, blank=True)

    # Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=160, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["employee", "-started_at"])]

    def __str__(self) -> str:
        return f"Session {self.employee.full_name} @ {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def total_seconds(self) -> int:
        return self.active_seconds + self.idle_seconds

    @property
    def activity_ratio(self) -> float:
        total = self.total_seconds
        if not total:
            return 0.0
        return round(self.active_seconds / total * 100, 1)

    def end(self) -> None:
        self.ended_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["ended_at", "is_active"])


class ActivitySnapshot(TimeStampedModel):
    """A periodic point-in-time snapshot within a session."""

    session = models.ForeignKey(
        ActivitySession, on_delete=models.CASCADE, related_name="snapshots"
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="activity_snapshots",
    )
    captured_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_active = models.BooleanField(default=True)
    active_application = models.CharField(max_length=200, blank=True)
    active_window_title = models.CharField(max_length=255, blank=True)
    active_website = models.CharField(max_length=255, blank=True)
    keyboard_events = models.PositiveIntegerField(default=0)
    mouse_events = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self) -> str:
        return f"Snapshot {self.employee.full_name} @ {self.captured_at:%H:%M}"


class ApplicationUsage(TimeStampedModel):
    """Aggregated time spent in a desktop application on a given day."""

    class Category(models.TextChoices):
        PRODUCTIVE = "productive", "Productive"
        NEUTRAL = "neutral", "Neutral"
        UNPRODUCTIVE = "unproductive", "Unproductive"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="application_usage",
    )
    date = models.DateField(db_index=True)
    application = models.CharField(max_length=200)
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.NEUTRAL
    )
    seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-seconds"]
        unique_together = ("employee", "date", "application")

    def __str__(self) -> str:
        return f"{self.application} — {self.employee.full_name}"

    @property
    def hours(self) -> float:
        return round(self.seconds / 3600, 2)


class WebsiteUsage(TimeStampedModel):
    class Category(models.TextChoices):
        PRODUCTIVE = "productive", "Productive"
        NEUTRAL = "neutral", "Neutral"
        UNPRODUCTIVE = "unproductive", "Unproductive"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="website_usage",
    )
    date = models.DateField(db_index=True)
    domain = models.CharField(max_length=200)
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.NEUTRAL
    )
    seconds = models.PositiveIntegerField(default=0)
    visits = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-seconds"]
        unique_together = ("employee", "date", "domain")

    def __str__(self) -> str:
        return f"{self.domain} — {self.employee.full_name}"

    @property
    def hours(self) -> float:
        return round(self.seconds / 3600, 2)


class DeviceMetric(TimeStampedModel):
    """Point-in-time device telemetry (CPU/RAM/disk/battery/network)."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="device_metrics",
    )
    session = models.ForeignKey(
        ActivitySession,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="metrics",
    )
    captured_at = models.DateTimeField(default=timezone.now, db_index=True)

    cpu_percent = models.FloatField(default=0)
    ram_percent = models.FloatField(default=0)
    disk_percent = models.FloatField(default=0)
    battery_percent = models.FloatField(null=True, blank=True)
    is_charging = models.BooleanField(default=False)

    network_status = models.CharField(max_length=40, blank=True)
    download_mbps = models.FloatField(default=0)
    upload_mbps = models.FloatField(default=0)
    ping_ms = models.FloatField(default=0)

    usb_devices = models.PositiveSmallIntegerField(default=0)
    printer_jobs = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-captured_at"]

    def __str__(self) -> str:
        return f"Metrics {self.employee.full_name} @ {self.captured_at:%H:%M}"
