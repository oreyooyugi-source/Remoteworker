"""Models for time entries and timesheets."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.constants import ApprovalStatus
from apps.core.models import TimeStampedModel


class TimeEntry(TimeStampedModel):
    """A single tracked interval of work, timed or entered manually."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="time_entries",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
    )
    timesheet = models.ForeignKey(
        "timetracking.Timesheet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entries",
    )

    description = models.CharField(max_length=255, blank=True)
    start_time = models.DateTimeField(default=timezone.now, db_index=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    is_billable = models.BooleanField(default=True)
    is_manual = models.BooleanField(default=False)
    is_running = models.BooleanField(default=False, db_index=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-start_time"]
        verbose_name_plural = "Time entries"
        indexes = [
            models.Index(fields=["employee", "-start_time"]),
            models.Index(fields=["is_running"]),
        ]

    def __str__(self) -> str:
        return f"{self.employee.full_name} — {self.description or 'Work'}"

    @property
    def duration_hours(self) -> float:
        return round(self.duration_seconds / 3600, 2)

    @property
    def billable_amount(self):
        return round((self.duration_seconds / 3600) * float(self.hourly_rate), 2)

    def stop(self) -> None:
        if self.is_running:
            self.end_time = timezone.now()
            self.duration_seconds = int(
                (self.end_time - self.start_time).total_seconds()
            )
            self.is_running = False
            self.save(update_fields=["end_time", "duration_seconds", "is_running"])

    def recompute(self) -> None:
        if self.start_time and self.end_time:
            self.duration_seconds = max(
                int((self.end_time - self.start_time).total_seconds()), 0
            )


class Timesheet(TimeStampedModel):
    """A weekly (or arbitrary period) collection of time entries for approval."""

    class Period(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
        CUSTOM = "custom", "Custom"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="timesheets",
    )
    period_type = models.CharField(
        max_length=10, choices=Period.choices, default=Period.WEEKLY
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=12,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    total_seconds = models.PositiveIntegerField(default=0)
    billable_seconds = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_timesheets",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-start_date"]
        unique_together = ("employee", "start_date", "end_date")

    def __str__(self) -> str:
        return f"{self.employee.full_name} — {self.start_date} to {self.end_date}"

    @property
    def total_hours(self) -> float:
        return round(self.total_seconds / 3600, 2)

    @property
    def billable_hours(self) -> float:
        return round(self.billable_seconds / 3600, 2)

    @property
    def non_billable_hours(self) -> float:
        return round((self.total_seconds - self.billable_seconds) / 3600, 2)

    def recompute(self) -> None:
        entries = self.entries.all()
        self.total_seconds = sum(e.duration_seconds for e in entries)
        self.billable_seconds = sum(
            e.duration_seconds for e in entries if e.is_billable
        )

    def submit(self) -> None:
        self.status = ApprovalStatus.PENDING
        self.submitted_at = timezone.now()
        self.save(update_fields=["status", "submitted_at"])

    def approve(self, approver, note: str = "") -> None:
        self.status = ApprovalStatus.APPROVED
        self.approver = approver
        self.approved_at = timezone.now()
        self.note = note
        self.save()

    def reject(self, approver, note: str = "") -> None:
        self.status = ApprovalStatus.REJECTED
        self.approver = approver
        self.approved_at = timezone.now()
        self.note = note
        self.save()
