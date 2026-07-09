"""Business logic for attendance operations."""
from __future__ import annotations

import datetime

from django.db import transaction
from django.utils import timezone

from apps.attendance.models import (
    AttendanceRecord,
    AttendanceStatus,
    BreakRecord,
    Shift,
)
from apps.core.constants import OnlineStatus
from apps.core.utils import get_client_ip


def get_or_create_today(employee, for_date=None) -> AttendanceRecord:
    for_date = for_date or timezone.localdate()
    record, _created = AttendanceRecord.objects.get_or_create(
        employee=employee, date=for_date
    )
    return record


@transaction.atomic
def clock_in(employee, request=None, latitude=None, longitude=None) -> AttendanceRecord:
    """Clock an employee in for the current day."""
    record = get_or_create_today(employee)
    if record.clock_in and not record.clock_out:
        return record  # already clocked in

    now = timezone.now()
    record.clock_in = now
    record.clock_out = None
    record.status = AttendanceStatus.PRESENT

    # Determine lateness against the default shift.
    shift = Shift.objects.filter(is_active=True).first()
    record.shift = shift
    if shift:
        expected = timezone.make_aware(
            datetime.datetime.combine(timezone.localdate(), shift.start_time)
        )
        grace = datetime.timedelta(minutes=shift.grace_period_minutes)
        if now > expected + grace:
            record.is_late = True
            record.late_minutes = int((now - expected).total_seconds() // 60)
            record.status = AttendanceStatus.LATE

    if request is not None:
        record.clock_in_ip = get_client_ip(request)
    if latitude is not None:
        record.clock_in_latitude = latitude
    if longitude is not None:
        record.clock_in_longitude = longitude

    record.save()
    employee.set_online_status(OnlineStatus.WORKING)
    return record


@transaction.atomic
def clock_out(employee) -> AttendanceRecord | None:
    """Clock an employee out and finalise the day's totals."""
    record = AttendanceRecord.objects.filter(
        employee=employee, date=timezone.localdate()
    ).first()
    if not record or not record.clock_in:
        return None

    # Close any open break first.
    open_break = record.breaks.filter(end_time__isnull=True).first()
    if open_break:
        open_break.end()

    record.clock_out = timezone.now()

    shift = record.shift or Shift.objects.filter(is_active=True).first()
    if shift:
        expected_end = timezone.make_aware(
            datetime.datetime.combine(timezone.localdate(), shift.end_time)
        )
        if record.clock_out < expected_end:
            record.is_early_departure = True
            record.early_minutes = int(
                (expected_end - record.clock_out).total_seconds() // 60
            )

    record.recompute()
    record.save()
    employee.set_online_status(OnlineStatus.OFFLINE)
    return record


@transaction.atomic
def start_break(employee, break_type="short") -> BreakRecord | None:
    record = AttendanceRecord.objects.filter(
        employee=employee, date=timezone.localdate()
    ).first()
    if not record or not record.is_clocked_in:
        return None
    if record.breaks.filter(end_time__isnull=True).exists():
        return record.breaks.filter(end_time__isnull=True).first()
    employee.set_online_status(OnlineStatus.BREAK)
    return BreakRecord.objects.create(attendance=record, break_type=break_type)


@transaction.atomic
def end_break(employee) -> BreakRecord | None:
    record = AttendanceRecord.objects.filter(
        employee=employee, date=timezone.localdate()
    ).first()
    if not record:
        return None
    open_break = record.breaks.filter(end_time__isnull=True).first()
    if open_break:
        open_break.end()
        record.recompute()
        record.save(update_fields=["break_seconds", "worked_seconds", "overtime_seconds"])
        employee.set_online_status(OnlineStatus.WORKING)
    return open_break


def current_status(employee) -> dict:
    """Return the employee's current clock/break state for the UI."""
    record = AttendanceRecord.objects.filter(
        employee=employee, date=timezone.localdate()
    ).first()
    if not record:
        return {"state": "out", "record": None, "on_break": False}
    on_break = record.breaks.filter(end_time__isnull=True).exists()
    if record.is_clocked_in:
        state = "break" if on_break else "in"
    elif record.clock_out:
        state = "done"
    else:
        state = "out"
    return {"state": state, "record": record, "on_break": on_break}


def monthly_summary(employee, year: int, month: int) -> dict:
    records = AttendanceRecord.objects.filter(
        employee=employee, date__year=year, date__month=month
    )
    present = records.filter(
        status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.REMOTE]
    ).count()
    absent = records.filter(status=AttendanceStatus.ABSENT).count()
    late = records.filter(is_late=True).count()
    total_seconds = sum(r.worked_seconds for r in records)
    overtime = sum(r.overtime_seconds for r in records)
    return {
        "present": present,
        "absent": absent,
        "late": late,
        "on_leave": records.filter(status=AttendanceStatus.ON_LEAVE).count(),
        "total_hours": round(total_seconds / 3600, 1),
        "overtime_hours": round(overtime / 3600, 1),
        "records": records,
    }
