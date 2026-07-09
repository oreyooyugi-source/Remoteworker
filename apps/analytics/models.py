"""Models for analytics snapshots."""
from __future__ import annotations

from django.db import models

from apps.core.models import TimeStampedModel


class KPISnapshot(TimeStampedModel):
    """A daily snapshot of company-wide KPIs for fast trend charts."""

    date = models.DateField(unique=True, db_index=True)
    headcount = models.PositiveIntegerField(default=0)
    active_employees = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    avg_productivity = models.FloatField(default=0)
    avg_activity = models.FloatField(default=0)
    total_hours = models.FloatField(default=0)
    overtime_hours = models.FloatField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    active_projects = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date"]
        verbose_name = "KPI snapshot"
        verbose_name_plural = "KPI snapshots"

    def __str__(self) -> str:
        return f"KPIs {self.date}"

    @property
    def attendance_rate(self) -> float:
        total = self.present_count + self.absent_count
        if not total:
            return 0.0
        return round(self.present_count / total * 100, 1)
