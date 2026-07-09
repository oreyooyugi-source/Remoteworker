"""Models for saved and generated reports."""
from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ReportType(models.TextChoices):
    EMPLOYEE = "employee", "Employee Report"
    DEPARTMENT = "department", "Department Report"
    ATTENDANCE = "attendance", "Attendance Report"
    PRODUCTIVITY = "productivity", "Productivity Report"
    TIMESHEET = "timesheet", "Timesheet Report"
    PROJECT = "project", "Project Report"
    PAYROLL = "payroll", "Payroll Report"
    AUDIT = "audit", "Audit Report"


class ReportFormat(models.TextChoices):
    CSV = "csv", "CSV"
    XLSX = "xlsx", "Excel"
    PDF = "pdf", "PDF"


class Report(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    export_format = models.CharField(
        max_length=8, choices=ReportFormat.choices, default=ReportFormat.CSV
    )
    parameters = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reports",
    )
    file = models.FileField(upload_to="reports/", null=True, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    @property
    def icon(self) -> str:
        return {
            ReportFormat.CSV: "fa-file-csv",
            ReportFormat.XLSX: "fa-file-excel",
            ReportFormat.PDF: "fa-file-pdf",
        }.get(self.export_format, "fa-file")
