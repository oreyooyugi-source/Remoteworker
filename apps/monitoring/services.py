"""Business logic for the monitoring app."""
from __future__ import annotations

from django.db.models import Sum
from django.utils import timezone

from apps.core.constants import OnlineStatus
from apps.employees.models import Employee
from apps.monitoring.models import (
    ActivitySession,
    ApplicationUsage,
    WebsiteUsage,
)


def live_overview() -> dict:
    """Return real-time counts of employee presence states."""
    employees = Employee.objects.select_related("user", "department")
    buckets = {
        "online": [],
        "working": [],
        "idle": [],
        "break": [],
        "meeting": [],
        "offline": [],
    }
    for employee in employees:
        key = employee.online_status
        buckets.setdefault(key, []).append(employee)

    working = buckets.get("working", []) + buckets.get("online", [])
    return {
        "working": working,
        "idle": buckets.get("idle", []),
        "on_break": buckets.get("break", []),
        "in_meeting": buckets.get("meeting", []),
        "offline": buckets.get("offline", []),
        "counts": {
            "working": len(working),
            "idle": len(buckets.get("idle", [])),
            "break": len(buckets.get("break", [])),
            "meeting": len(buckets.get("meeting", [])),
            "offline": len(buckets.get("offline", [])),
            "total": employees.count(),
        },
    }


def employee_activity(employee, for_date=None) -> dict:
    """Return an activity summary for one employee on a given day."""
    for_date = for_date or timezone.localdate()
    sessions = ActivitySession.objects.filter(
        employee=employee, started_at__date=for_date
    )
    active = sessions.aggregate(v=Sum("active_seconds"))["v"] or 0
    idle = sessions.aggregate(v=Sum("idle_seconds"))["v"] or 0
    keyboard = sessions.aggregate(v=Sum("keyboard_events"))["v"] or 0
    mouse = sessions.aggregate(v=Sum("mouse_events"))["v"] or 0

    top_apps = ApplicationUsage.objects.filter(
        employee=employee, date=for_date
    ).order_by("-seconds")[:8]
    top_sites = WebsiteUsage.objects.filter(
        employee=employee, date=for_date
    ).order_by("-seconds")[:8]

    total = active + idle
    return {
        "active_seconds": active,
        "idle_seconds": idle,
        "active_hours": round(active / 3600, 2),
        "idle_hours": round(idle / 3600, 2),
        "activity_ratio": round(active / total * 100, 1) if total else 0,
        "keyboard_events": keyboard,
        "mouse_events": mouse,
        "top_apps": top_apps,
        "top_sites": top_sites,
        "sessions": sessions,
        "latest_session": sessions.order_by("-started_at").first(),
    }


def set_status(employee, status: str) -> None:
    if status in OnlineStatus.values:
        employee.set_online_status(status)
