"""Business logic for time tracking."""
from __future__ import annotations

import datetime

from django.db import transaction
from django.utils import timezone

from apps.core.utils import start_of_week
from apps.timetracking.models import TimeEntry, Timesheet


def get_running_entry(employee) -> TimeEntry | None:
    return TimeEntry.objects.filter(employee=employee, is_running=True).first()


@transaction.atomic
def start_timer(employee, description="", project=None, task=None, billable=True) -> TimeEntry:
    """Start a new timer, stopping any already-running entry first."""
    running = get_running_entry(employee)
    if running:
        running.stop()

    rate = employee.hourly_rate or 0
    return TimeEntry.objects.create(
        employee=employee,
        description=description,
        project=project,
        task=task,
        is_billable=billable,
        is_running=True,
        start_time=timezone.now(),
        hourly_rate=rate,
    )


def stop_timer(employee) -> TimeEntry | None:
    running = get_running_entry(employee)
    if running:
        running.stop()
        _attach_to_timesheet(running)
    return running


@transaction.atomic
def add_manual_entry(
    employee, start_time, end_time, description="", project=None, task=None, billable=True
) -> TimeEntry:
    entry = TimeEntry(
        employee=employee,
        description=description,
        project=project,
        task=task,
        start_time=start_time,
        end_time=end_time,
        is_billable=billable,
        is_manual=True,
        is_running=False,
        hourly_rate=employee.hourly_rate or 0,
    )
    entry.recompute()
    entry.save()
    _attach_to_timesheet(entry)
    return entry


def _attach_to_timesheet(entry: TimeEntry) -> None:
    """Attach an entry to the appropriate weekly timesheet and update totals."""
    day = timezone.localtime(entry.start_time).date()
    week_start = start_of_week(day)
    week_end = week_start + datetime.timedelta(days=6)
    timesheet, _created = Timesheet.objects.get_or_create(
        employee=entry.employee,
        start_date=week_start,
        end_date=week_end,
        defaults={"period_type": Timesheet.Period.WEEKLY},
    )
    entry.timesheet = timesheet
    entry.save(update_fields=["timesheet"])
    timesheet.recompute()
    timesheet.save(update_fields=["total_seconds", "billable_seconds"])


def weekly_summary(employee, week_start=None) -> dict:
    week_start = week_start or start_of_week()
    week_end = week_start + datetime.timedelta(days=6)
    entries = TimeEntry.objects.filter(
        employee=employee,
        start_time__date__gte=week_start,
        start_time__date__lte=week_end,
    )
    by_day = {}
    for offset in range(7):
        day = week_start + datetime.timedelta(days=offset)
        day_entries = [e for e in entries if timezone.localtime(e.start_time).date() == day]
        by_day[day.strftime("%a")] = round(
            sum(e.duration_seconds for e in day_entries) / 3600, 2
        )
    total = sum(e.duration_seconds for e in entries)
    billable = sum(e.duration_seconds for e in entries if e.is_billable)
    return {
        "by_day": by_day,
        "total_hours": round(total / 3600, 2),
        "billable_hours": round(billable / 3600, 2),
        "entries": entries,
        "week_start": week_start,
        "week_end": week_end,
    }
