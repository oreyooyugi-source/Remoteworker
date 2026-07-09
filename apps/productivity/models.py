"""Models for productivity scoring."""
from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel


class ProductivityRecord(TimeStampedModel):
    """A per-employee, per-day productivity scorecard."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="productivity_records",
    )
    date = models.DateField(db_index=True)

    # Component scores (0-100)
    productivity_score = models.FloatField(default=0)
    activity_score = models.FloatField(default=0)
    focus_score = models.FloatField(default=0)
    efficiency_score = models.FloatField(default=0)
    attendance_score = models.FloatField(default=0)

    # Raw time components (seconds)
    active_seconds = models.PositiveIntegerField(default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    focus_seconds = models.PositiveIntegerField(default=0)
    break_seconds = models.PositiveIntegerField(default=0)
    meeting_seconds = models.PositiveIntegerField(default=0)

    productive_seconds = models.PositiveIntegerField(default=0)
    neutral_seconds = models.PositiveIntegerField(default=0)
    unproductive_seconds = models.PositiveIntegerField(default=0)

    tasks_completed = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        unique_together = ("employee", "date")
        indexes = [models.Index(fields=["employee", "-date"])]

    def __str__(self) -> str:
        return f"{self.employee.full_name} — {self.date}: {self.productivity_score:.0f}%"

    @property
    def idle_percent(self) -> float:
        total = self.active_seconds + self.idle_seconds
        if not total:
            return 0.0
        return round(self.idle_seconds / total * 100, 1)

    @property
    def active_hours(self) -> float:
        return round(self.active_seconds / 3600, 2)

    @property
    def rating(self) -> str:
        score = self.productivity_score
        if score >= 85:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 50:
            return "Average"
        if score >= 30:
            return "Below Average"
        return "Poor"

    @property
    def rating_color(self) -> str:
        score = self.productivity_score
        if score >= 85:
            return "success"
        if score >= 70:
            return "info"
        if score >= 50:
            return "warning"
        return "danger"


class ProductivityGoal(TimeStampedModel):
    class Period(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="productivity_goals",
    )
    period = models.CharField(
        max_length=10, choices=Period.choices, default=Period.WEEKLY
    )
    target_score = models.FloatField(default=75)
    target_hours = models.DecimalField(max_digits=6, decimal_places=2, default=40)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Goal — {self.employee.full_name} ({self.get_period_display()})"
