"""Business logic for productivity scoring and insights."""
from __future__ import annotations

import datetime

from django.db.models import Avg, Sum
from django.utils import timezone

from apps.core.utils import percentage
from apps.productivity.models import ProductivityRecord


def compute_score(
    active_seconds: int,
    idle_seconds: int,
    productive_seconds: int,
    unproductive_seconds: int,
    focus_seconds: int,
    attendance_ok: bool = True,
) -> dict:
    """Compute the component scores and a weighted overall score."""
    total = active_seconds + idle_seconds
    activity_score = percentage(active_seconds, total) if total else 0

    classified = productive_seconds + unproductive_seconds
    efficiency_score = percentage(productive_seconds, classified) if classified else 50

    focus_score = percentage(focus_seconds, active_seconds) if active_seconds else 0
    attendance_score = 100 if attendance_ok else 60

    # Weighted overall productivity score.
    overall = (
        activity_score * 0.30
        + efficiency_score * 0.30
        + focus_score * 0.25
        + attendance_score * 0.15
    )
    return {
        "activity_score": round(activity_score, 1),
        "efficiency_score": round(efficiency_score, 1),
        "focus_score": round(focus_score, 1),
        "attendance_score": round(attendance_score, 1),
        "productivity_score": round(overall, 1),
    }


def recompute_for(employee, for_date=None) -> ProductivityRecord:
    """Rebuild an employee's productivity record for ``for_date`` from raw data."""
    for_date = for_date or timezone.localdate()

    from apps.monitoring.models import (
        ActivitySession,
        ApplicationUsage,
        WebsiteUsage,
    )

    sessions = ActivitySession.objects.filter(
        employee=employee, started_at__date=for_date
    )
    active = sessions.aggregate(v=Sum("active_seconds"))["v"] or 0
    idle = sessions.aggregate(v=Sum("idle_seconds"))["v"] or 0
    meeting = sessions.aggregate(v=Sum("meeting_seconds"))["v"] or 0
    breaks = sessions.aggregate(v=Sum("break_seconds"))["v"] or 0

    app_usage = ApplicationUsage.objects.filter(employee=employee, date=for_date)
    web_usage = WebsiteUsage.objects.filter(employee=employee, date=for_date)

    productive = (
        (app_usage.filter(category="productive").aggregate(v=Sum("seconds"))["v"] or 0)
        + (web_usage.filter(category="productive").aggregate(v=Sum("seconds"))["v"] or 0)
    )
    unproductive = (
        (app_usage.filter(category="unproductive").aggregate(v=Sum("seconds"))["v"] or 0)
        + (web_usage.filter(category="unproductive").aggregate(v=Sum("seconds"))["v"] or 0)
    )
    neutral = (
        (app_usage.filter(category="neutral").aggregate(v=Sum("seconds"))["v"] or 0)
        + (web_usage.filter(category="neutral").aggregate(v=Sum("seconds"))["v"] or 0)
    )

    # Focus time: continuous active time excluding meetings.
    focus = max(active - meeting, 0)

    # Attendance check.
    attendance_ok = True
    try:
        from apps.attendance.models import AttendanceRecord, AttendanceStatus

        record = AttendanceRecord.objects.filter(
            employee=employee, date=for_date
        ).first()
        attendance_ok = bool(
            record and record.status != AttendanceStatus.ABSENT
        )
    except Exception:  # noqa: BLE001
        pass

    scores = compute_score(active, idle, productive, unproductive, focus, attendance_ok)

    # Tasks completed today.
    tasks_completed = 0
    try:
        from apps.tasks.models import Task, TaskStatus

        tasks_completed = Task.objects.filter(
            assignees=employee,
            status=TaskStatus.DONE,
            completed_at__date=for_date,
        ).count()
    except Exception:  # noqa: BLE001
        pass

    record, _created = ProductivityRecord.objects.update_or_create(
        employee=employee,
        date=for_date,
        defaults={
            **scores,
            "active_seconds": active,
            "idle_seconds": idle,
            "focus_seconds": focus,
            "break_seconds": breaks,
            "meeting_seconds": meeting,
            "productive_seconds": productive,
            "neutral_seconds": neutral,
            "unproductive_seconds": unproductive,
            "tasks_completed": tasks_completed,
        },
    )
    return record


def trend(employee, days: int = 14) -> dict:
    """Return a productivity trend series for charts."""
    end = timezone.localdate()
    start = end - datetime.timedelta(days=days - 1)
    records = {
        r.date: r
        for r in ProductivityRecord.objects.filter(
            employee=employee, date__gte=start, date__lte=end
        )
    }
    labels, scores, active_hours = [], [], []
    for offset in range(days):
        day = start + datetime.timedelta(days=offset)
        labels.append(day.strftime("%d %b"))
        record = records.get(day)
        scores.append(round(record.productivity_score, 1) if record else 0)
        active_hours.append(record.active_hours if record else 0)
    return {"labels": labels, "scores": scores, "active_hours": active_hours}


def leaderboard(limit: int = 10, days: int = 7) -> list[dict]:
    """Top employees by average productivity over the period."""
    start = timezone.localdate() - datetime.timedelta(days=days)
    rows = (
        ProductivityRecord.objects.filter(date__gte=start)
        .values("employee")
        .annotate(avg_score=Avg("productivity_score"), active=Sum("active_seconds"))
        .order_by("-avg_score")[:limit]
    )
    from apps.employees.models import Employee

    result = []
    for row in rows:
        employee = Employee.objects.filter(pk=row["employee"]).select_related("user").first()
        if employee:
            result.append(
                {
                    "employee": employee,
                    "avg_score": round(row["avg_score"] or 0, 1),
                    "active_hours": round((row["active"] or 0) / 3600, 1),
                }
            )
    return result
