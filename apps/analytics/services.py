"""Analytics aggregation services for dashboards and charts."""
from __future__ import annotations

import datetime

from django.db.models import Avg, Count, Sum
from django.utils import timezone


def company_kpis() -> dict:
    """Headline KPIs shown at the top of the analytics dashboard."""
    from apps.employees.models import Employee
    from apps.core.constants import EmployeeStatus, OnlineStatus

    employees = Employee.objects.all()
    total = employees.count()
    active = employees.filter(status=EmployeeStatus.ACTIVE).count()
    online = employees.filter(online_status=OnlineStatus.WORKING).count()

    avg_prod = 0
    try:
        from apps.productivity.models import ProductivityRecord

        since = timezone.localdate() - datetime.timedelta(days=7)
        avg_prod = round(
            ProductivityRecord.objects.filter(date__gte=since).aggregate(
                v=Avg("productivity_score")
            )["v"]
            or 0,
            1,
        )
    except Exception:  # noqa: BLE001
        pass

    active_projects = 0
    try:
        from apps.projects.models import Project, ProjectStatus

        active_projects = Project.objects.filter(status=ProjectStatus.ACTIVE).count()
    except Exception:  # noqa: BLE001
        pass

    return {
        "headcount": total,
        "active": active,
        "online": online,
        "avg_productivity": avg_prod,
        "active_projects": active_projects,
        "utilization": round(online / total * 100, 1) if total else 0,
    }


def headcount_by_department() -> dict:
    from apps.employees.models import Department

    rows = (
        Department.objects.annotate(total=Count("employees"))
        .filter(is_active=True)
        .order_by("-total")[:12]
    )
    return {
        "labels": [d.name for d in rows],
        "data": [d.total for d in rows],
        "colors": [d.color for d in rows],
    }


def productivity_distribution() -> dict:
    """Bucket the latest productivity scores into rating bands."""
    buckets = {"Excellent": 0, "Good": 0, "Average": 0, "Below Average": 0, "Poor": 0}
    try:
        from apps.productivity.models import ProductivityRecord

        since = timezone.localdate() - datetime.timedelta(days=7)
        for record in ProductivityRecord.objects.filter(date__gte=since):
            buckets[record.rating] = buckets.get(record.rating, 0) + 1
    except Exception:  # noqa: BLE001
        pass
    return {"labels": list(buckets.keys()), "data": list(buckets.values())}


def attendance_trend(days: int = 30) -> dict:
    labels, present, absent = [], [], []
    try:
        from apps.attendance.models import AttendanceRecord, AttendanceStatus

        end = timezone.localdate()
        start = end - datetime.timedelta(days=days - 1)
        for offset in range(days):
            day = start + datetime.timedelta(days=offset)
            labels.append(day.strftime("%d %b"))
            day_qs = AttendanceRecord.objects.filter(date=day)
            present.append(
                day_qs.filter(
                    status__in=[
                        AttendanceStatus.PRESENT,
                        AttendanceStatus.LATE,
                        AttendanceStatus.REMOTE,
                    ]
                ).count()
            )
            absent.append(day_qs.filter(status=AttendanceStatus.ABSENT).count())
    except Exception:  # noqa: BLE001
        pass
    return {"labels": labels, "present": present, "absent": absent}


def productivity_heatmap(days: int = 28) -> dict:
    """Return a day-of-week x week grid of average productivity."""
    grid = []
    try:
        from apps.productivity.models import ProductivityRecord

        end = timezone.localdate()
        start = end - datetime.timedelta(days=days - 1)
        records = ProductivityRecord.objects.filter(date__gte=start, date__lte=end)
        by_date: dict[datetime.date, list] = {}
        for r in records:
            by_date.setdefault(r.date, []).append(r.productivity_score)
        for offset in range(days):
            day = start + datetime.timedelta(days=offset)
            scores = by_date.get(day, [])
            avg = round(sum(scores) / len(scores), 1) if scores else 0
            grid.append({"date": day.isoformat(), "weekday": day.weekday(), "value": avg})
    except Exception:  # noqa: BLE001
        pass
    return {"grid": grid}


def department_productivity() -> dict:
    """Average productivity per department for a comparison bar chart."""
    labels, data = [], []
    try:
        from apps.employees.models import Department
        from apps.productivity.models import ProductivityRecord

        since = timezone.localdate() - datetime.timedelta(days=30)
        for dept in Department.objects.filter(is_active=True)[:12]:
            avg = ProductivityRecord.objects.filter(
                employee__department=dept, date__gte=since
            ).aggregate(v=Avg("productivity_score"))["v"]
            if avg is not None:
                labels.append(dept.name)
                data.append(round(avg, 1))
    except Exception:  # noqa: BLE001
        pass
    return {"labels": labels, "data": data}


def hours_trend(days: int = 14) -> dict:
    labels, hours = [], []
    try:
        from apps.timetracking.models import TimeEntry

        end = timezone.localdate()
        start = end - datetime.timedelta(days=days - 1)
        for offset in range(days):
            day = start + datetime.timedelta(days=offset)
            labels.append(day.strftime("%d %b"))
            seconds = (
                TimeEntry.objects.filter(start_time__date=day).aggregate(
                    v=Sum("duration_seconds")
                )["v"]
                or 0
            )
            hours.append(round(seconds / 3600, 1))
    except Exception:  # noqa: BLE001
        pass
    return {"labels": labels, "hours": hours}


def forecast_productivity(days: int = 7) -> dict:
    """Naive linear forecast of productivity based on the recent trend."""
    from apps.productivity.services import trend as prod_trend  # noqa: F401

    try:
        from apps.productivity.models import ProductivityRecord

        since = timezone.localdate() - datetime.timedelta(days=14)
        series = list(
            ProductivityRecord.objects.filter(date__gte=since)
            .values("date")
            .annotate(v=Avg("productivity_score"))
            .order_by("date")
        )
        values = [row["v"] or 0 for row in series]
        if len(values) < 2:
            return {"labels": [], "forecast": []}
        # Simple least-squares slope.
        n = len(values)
        xs = list(range(n))
        mean_x = sum(xs) / n
        mean_y = sum(values) / n
        denom = sum((x - mean_x) ** 2 for x in xs) or 1
        slope = sum((xs[i] - mean_x) * (values[i] - mean_y) for i in range(n)) / denom
        intercept = mean_y - slope * mean_x
        labels, forecast = [], []
        for i in range(days):
            x = n + i
            labels.append((timezone.localdate() + datetime.timedelta(days=i)).strftime("%d %b"))
            forecast.append(round(max(0, min(100, slope * x + intercept)), 1))
        return {"labels": labels, "forecast": forecast}
    except Exception:  # noqa: BLE001
        return {"labels": [], "forecast": []}
