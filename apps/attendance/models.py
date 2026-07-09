"""Models for attendance, shifts, breaks and leave."""
from __future__ import annotations

import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.constants import ApprovalStatus
from apps.core.models import TimeStampedModel


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    HALF_DAY = "half_day", "Half Day"
    ON_LEAVE = "on_leave", "On Leave"
    HOLIDAY = "holiday", "Holiday"
    WEEKEND = "weekend", "Weekend"
    REMOTE = "remote", "Remote"


class Shift(TimeStampedModel):
    class ShiftType(models.TextChoices):
        DAY = "day", "Day Shift"
        NIGHT = "night", "Night Shift"
        FLEXIBLE = "flexible", "Flexible"
        ROTATING = "rotating", "Rotating"

    name = models.CharField(max_length=120)
    shift_type = models.CharField(
        max_length=20, choices=ShiftType.choices, default=ShiftType.DAY
    )
    start_time = models.TimeField(default="09:00")
    end_time = models.TimeField(default="17:00")
    break_minutes = models.PositiveIntegerField(default=60)
    grace_period_minutes = models.PositiveIntegerField(default=10)
    is_night_shift = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def expected_hours(self) -> float:
        start = datetime.datetime.combine(datetime.date.today(), self.start_time)
        end = datetime.datetime.combine(datetime.date.today(), self.end_time)
        if self.is_night_shift or end <= start:
            end += datetime.timedelta(days=1)
        total = (end - start).total_seconds() / 3600
        return round(total - (self.break_minutes / 60), 2)


class AttendanceRecord(TimeStampedModel):
    """One row per employee per day summarising their attendance."""

    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField(db_index=True)
    shift = models.ForeignKey(
        Shift, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=16,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT,
        db_index=True,
    )
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)

    worked_seconds = models.PositiveIntegerField(default=0)
    break_seconds = models.PositiveIntegerField(default=0)
    overtime_seconds = models.PositiveIntegerField(default=0)

    is_late = models.BooleanField(default=False)
    late_minutes = models.PositiveIntegerField(default=0)
    is_early_departure = models.BooleanField(default=False)
    early_minutes = models.PositiveIntegerField(default=0)

    clock_in_ip = models.GenericIPAddressField(null=True, blank=True)
    clock_in_latitude = models.FloatField(null=True, blank=True)
    clock_in_longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("employee", "date")
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["employee", "-date"]),
        ]

    def __str__(self) -> str:
        return f"{self.employee.full_name} — {self.date} ({self.get_status_display()})"

    @property
    def worked_hours(self) -> float:
        return round(self.worked_seconds / 3600, 2)

    @property
    def is_clocked_in(self) -> bool:
        return self.clock_in is not None and self.clock_out is None

    def recompute(self) -> None:
        """Recalculate worked/overtime seconds from clock times and breaks."""
        if self.clock_in and self.clock_out:
            gross = int((self.clock_out - self.clock_in).total_seconds())
            break_total = sum(
                b.duration_seconds for b in self.breaks.all()
            )
            self.break_seconds = break_total
            self.worked_seconds = max(gross - break_total, 0)
            standard = 8 * 3600
            self.overtime_seconds = max(self.worked_seconds - standard, 0)


class BreakRecord(TimeStampedModel):
    class BreakType(models.TextChoices):
        LUNCH = "lunch", "Lunch"
        SHORT = "short", "Short Break"
        MEETING = "meeting", "Meeting"
        PERSONAL = "personal", "Personal"

    attendance = models.ForeignKey(
        AttendanceRecord, on_delete=models.CASCADE, related_name="breaks"
    )
    break_type = models.CharField(
        max_length=16, choices=BreakType.choices, default=BreakType.SHORT
    )
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-start_time"]

    def __str__(self) -> str:
        return f"{self.get_break_type_display()} — {self.attendance.employee.full_name}"

    def end(self) -> None:
        self.end_time = timezone.now()
        self.duration_seconds = int(
            (self.end_time - self.start_time).total_seconds()
        )
        self.save(update_fields=["end_time", "duration_seconds"])


class LeaveRequest(TimeStampedModel):
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="leave_requests",
    )
    leave_type = models.ForeignKey(
        "settings_app.LeaveType",
        on_delete=models.SET_NULL,
        null=True,
        related_name="requests",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    half_day = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=12,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_leaves",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.employee.full_name} leave {self.start_date}–{self.end_date}"

    @property
    def days(self) -> int:
        base = (self.end_date - self.start_date).days + 1
        if self.half_day:
            return max(base - 0.5, 0.5)
        return base

    def approve(self, approver, note: str = "") -> None:
        self.status = ApprovalStatus.APPROVED
        self.approver = approver
        self.approved_at = timezone.now()
        self.decision_note = note
        self.save()

    def reject(self, approver, note: str = "") -> None:
        self.status = ApprovalStatus.REJECTED
        self.approver = approver
        self.approved_at = timezone.now()
        self.decision_note = note
        self.save()


class AttendanceCorrectionRequest(TimeStampedModel):
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="correction_requests",
    )
    attendance = models.ForeignKey(
        AttendanceRecord,
        on_delete=models.CASCADE,
        related_name="correction_requests",
        null=True,
        blank=True,
    )
    date = models.DateField()
    requested_clock_in = models.DateTimeField(null=True, blank=True)
    requested_clock_out = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(
        max_length=12,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_corrections",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Correction — {self.employee.full_name} {self.date}"
