"""Aggregation services powering the main dashboards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.utils import timezone


@dataclass
class StatCard:
    """A single KPI card displayed on a dashboard."""

    label: str
    value: Any
    icon: str = "fa-chart-simple"
    color: str = "primary"
    trend: float | None = None
    subtitle: str = ""
    url: str = ""


@dataclass
class DashboardData:
    """Container for everything a dashboard template needs."""

    role_label: str = ""
    stat_cards: list[StatCard] = field(default_factory=list)
    charts: dict[str, Any] = field(default_factory=dict)
    tables: dict[str, Any] = field(default_factory=dict)


def _safe_count(callable_):
    try:
        return callable_()
    except Exception:  # noqa: BLE001
        return 0


def build_dashboard(user) -> DashboardData:
    """Assemble dashboard data appropriate for ``user``'s role."""
    from apps.core.constants import Role

    role = getattr(user, "role", Role.EMPLOYEE)
    if user.is_superuser or role in {Role.SUPER_ADMIN, Role.COMPANY_ADMIN}:
        return _admin_dashboard(user)
    if role == Role.HR_MANAGER:
        return _hr_dashboard(user)
    if role in {
        Role.DEPARTMENT_MANAGER,
        Role.PROJECT_MANAGER,
        Role.SUPERVISOR,
        Role.TEAM_LEAD,
    }:
        return _manager_dashboard(user)
    if role == Role.AUDITOR:
        return _auditor_dashboard(user)
    return _employee_dashboard(user)


# ---------------------------------------------------------------------------
# Role-specific builders
# ---------------------------------------------------------------------------
def _admin_dashboard(user) -> DashboardData:
    from django.contrib.auth import get_user_model

    from apps.core.constants import OnlineStatus

    User = get_user_model()
    data = DashboardData(role_label="Administrator")

    total_employees = _safe_count(lambda: _employee_model().objects.count())
    online = _safe_count(
        lambda: _employee_model()
        .objects.filter(online_status=OnlineStatus.ONLINE)
        .count()
    )
    departments = _safe_count(lambda: _department_model().objects.count())
    projects = _safe_count(lambda: _project_model().objects.count())

    data.stat_cards = [
        StatCard("Total Employees", total_employees, "fa-users", "primary"),
        StatCard("Online Now", online, "fa-circle-dot", "success"),
        StatCard("Departments", departments, "fa-sitemap", "info"),
        StatCard("Active Projects", projects, "fa-diagram-project", "warning"),
    ]
    data.charts = _attendance_trend_chart()
    return data


def _hr_dashboard(user) -> DashboardData:
    from apps.core.constants import EmployeeStatus

    data = DashboardData(role_label="HR Manager")
    total = _safe_count(lambda: _employee_model().objects.count())
    on_leave = _safe_count(
        lambda: _employee_model()
        .objects.filter(status=EmployeeStatus.ON_LEAVE)
        .count()
    )
    probation = _safe_count(
        lambda: _employee_model()
        .objects.filter(status=EmployeeStatus.PROBATION)
        .count()
    )
    data.stat_cards = [
        StatCard("Headcount", total, "fa-users", "primary"),
        StatCard("On Leave", on_leave, "fa-plane-departure", "warning"),
        StatCard("On Probation", probation, "fa-user-clock", "info"),
        StatCard("Pending Requests", _pending_leave_count(), "fa-inbox", "danger"),
    ]
    data.charts = _attendance_trend_chart()
    return data


def _manager_dashboard(user) -> DashboardData:
    data = DashboardData(role_label="Manager")
    employee = getattr(user, "employee_profile", None)
    team_size = 0
    if employee and employee.department_id:
        team_size = _safe_count(
            lambda: _employee_model()
            .objects.filter(department_id=employee.department_id)
            .count()
        )
    data.stat_cards = [
        StatCard("Team Size", team_size, "fa-people-group", "primary"),
        StatCard("Tasks Open", _open_task_count(user), "fa-list-check", "warning"),
        StatCard("Approvals", _pending_leave_count(), "fa-check-double", "info"),
        StatCard("Avg Productivity", f"{_avg_productivity()}%", "fa-bolt", "success"),
    ]
    data.charts = _attendance_trend_chart()
    return data


def _auditor_dashboard(user) -> DashboardData:
    data = DashboardData(role_label="Auditor")
    logs = _safe_count(lambda: _audit_model().objects.count())
    data.stat_cards = [
        StatCard("Audit Events", logs, "fa-shield-halved", "primary"),
        StatCard("Today's Events", _audit_today(), "fa-calendar-day", "info"),
        StatCard("Failed Logins", _failed_login_count(), "fa-triangle-exclamation", "danger"),
        StatCard("Reports", _report_count(), "fa-file-lines", "success"),
    ]
    return data


def _employee_dashboard(user) -> DashboardData:
    data = DashboardData(role_label="Employee")
    data.stat_cards = [
        StatCard("Hours Today", _hours_today(user), "fa-clock", "primary"),
        StatCard("My Tasks", _open_task_count(user), "fa-list-check", "warning"),
        StatCard("Productivity", f"{_avg_productivity(user)}%", "fa-bolt", "success"),
        StatCard("Notifications", _unread_notifications(user), "fa-bell", "info"),
    ]
    return data


# ---------------------------------------------------------------------------
# Lazy model accessors (avoid hard import cycles / migration issues)
# ---------------------------------------------------------------------------
def _employee_model():
    from apps.employees.models import Employee

    return Employee


def _department_model():
    from apps.employees.models import Department

    return Department


def _project_model():
    from apps.projects.models import Project

    return Project


def _audit_model():
    from apps.audit.models import AuditLog

    return AuditLog


# ---------------------------------------------------------------------------
# Small metric helpers (defensive)
# ---------------------------------------------------------------------------
def _pending_leave_count() -> int:
    def _q():
        from apps.attendance.models import LeaveRequest
        from apps.core.constants import ApprovalStatus

        return LeaveRequest.objects.filter(status=ApprovalStatus.PENDING).count()

    return _safe_count(_q)


def _open_task_count(user=None) -> int:
    def _q():
        from apps.tasks.models import Task

        qs = Task.objects.exclude(status__in=["done", "cancelled"])
        if user is not None and getattr(user, "employee_profile", None):
            qs = qs.filter(assignees=user.employee_profile)
        return qs.count()

    return _safe_count(_q)


def _avg_productivity(user=None) -> float:
    def _q():
        from django.db.models import Avg

        from apps.productivity.models import ProductivityRecord

        qs = ProductivityRecord.objects.all()
        if user is not None and getattr(user, "employee_profile", None):
            qs = qs.filter(employee=user.employee_profile)
        result = qs.aggregate(v=Avg("productivity_score"))["v"]
        return round(result or 0, 1)

    try:
        return _q()
    except Exception:  # noqa: BLE001
        return 0.0


def _hours_today(user) -> str:
    def _q():
        from apps.core.utils import format_duration
        from apps.timetracking.models import TimeEntry

        employee = getattr(user, "employee_profile", None)
        if not employee:
            return "0m"
        today = timezone.localdate()
        entries = TimeEntry.objects.filter(
            employee=employee, start_time__date=today
        )
        total = sum((e.duration_seconds or 0) for e in entries)
        return format_duration(total)

    try:
        return _q()
    except Exception:  # noqa: BLE001
        return "0m"


def _unread_notifications(user) -> int:
    def _q():
        from apps.notifications.models import Notification

        return Notification.objects.filter(recipient=user, is_read=False).count()

    return _safe_count(_q)


def _audit_today() -> int:
    def _q():
        from apps.audit.models import AuditLog

        return AuditLog.objects.filter(
            created_at__date=timezone.localdate()
        ).count()

    return _safe_count(_q)


def _failed_login_count() -> int:
    def _q():
        from apps.accounts.models import LoginAttempt

        return LoginAttempt.objects.filter(successful=False).count()

    return _safe_count(_q)


def _report_count() -> int:
    def _q():
        from apps.reports.models import Report

        return Report.objects.count()

    return _safe_count(_q)


def _attendance_trend_chart() -> dict:
    """Return a 7-day attendance trend suitable for Chart.js."""
    labels: list[str] = []
    present: list[int] = []
    try:
        from apps.attendance.models import AttendanceRecord

        for offset in range(6, -1, -1):
            day = timezone.localdate() - timezone.timedelta(days=offset)
            labels.append(day.strftime("%a"))
            present.append(
                AttendanceRecord.objects.filter(
                    date=day, status="present"
                ).count()
            )
    except Exception:  # noqa: BLE001
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        present = [0, 0, 0, 0, 0, 0, 0]
    return {"attendance_trend": {"labels": labels, "present": present}}
