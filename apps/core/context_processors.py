"""Template context processors for the core app."""
from __future__ import annotations

from django.conf import settings

from apps.core import permissions as perms


def site_context(request) -> dict:
    """Expose global application metadata to every template."""
    rwt = getattr(settings, "RWT", {})
    return {
        "APP_NAME": rwt.get("APP_NAME", "Remote Worker Tracker"),
        "APP_SHORT_NAME": rwt.get("APP_SHORT_NAME", "RWT"),
        "APP_VERSION": rwt.get("APP_VERSION", "1.0.0"),
    }


def _nav_item(label, icon, url_name, module, badge=None, children=None):
    return {
        "label": label,
        "icon": icon,
        "url_name": url_name,
        "module": module,
        "badge": badge,
        "children": children or [],
    }


def navigation(request) -> dict:
    """Build the sidebar navigation, filtered by the user's permissions."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"nav_sections": []}

    sections = [
        {
            "heading": "Overview",
            "items": [
                _nav_item("Dashboard", "fa-gauge-high", "core:dashboard", "dashboard"),
                _nav_item("Analytics", "fa-chart-line", "analytics:dashboard", "analytics"),
                _nav_item("Live Monitoring", "fa-satellite-dish", "monitoring:live", "monitoring"),
            ],
        },
        {
            "heading": "Workforce",
            "items": [
                _nav_item("Employees", "fa-users", "employees:list", "employees"),
                _nav_item("Departments", "fa-sitemap", "employees:department_list", "employees"),
                _nav_item("Teams", "fa-people-group", "employees:team_list", "employees"),
                _nav_item("Attendance", "fa-calendar-check", "attendance:dashboard", "attendance"),
                _nav_item("Leave", "fa-plane-departure", "attendance:leave_list", "attendance"),
            ],
        },
        {
            "heading": "Productivity",
            "items": [
                _nav_item("Time Tracking", "fa-stopwatch", "timetracking:dashboard", "timetracking"),
                _nav_item("Timesheets", "fa-table-list", "timetracking:timesheet_list", "timetracking"),
                _nav_item("Productivity", "fa-bolt", "productivity:dashboard", "productivity"),
                _nav_item("Screenshots", "fa-camera", "screenshots:list", "screenshots"),
            ],
        },
        {
            "heading": "Delivery",
            "items": [
                _nav_item("Projects", "fa-diagram-project", "projects:list", "projects"),
                _nav_item("Tasks", "fa-list-check", "tasks:board", "tasks"),
            ],
        },
        {
            "heading": "Finance",
            "items": [
                _nav_item("Payroll", "fa-money-check-dollar", "payroll:dashboard", "payroll"),
            ],
        },
        {
            "heading": "Insights",
            "items": [
                _nav_item("Reports", "fa-file-lines", "reports:list", "reports"),
                _nav_item("Audit Log", "fa-shield-halved", "audit:list", "audit"),
            ],
        },
        {
            "heading": "System",
            "items": [
                _nav_item("Settings", "fa-gear", "settings_app:index", "settings"),
            ],
        },
    ]

    # Filter items by module access.
    filtered_sections = []
    for section in sections:
        items = [
            item
            for item in section["items"]
            if perms.can_access_module(user, item["module"])
        ]
        if items:
            filtered_sections.append({"heading": section["heading"], "items": items})

    return {"nav_sections": filtered_sections}
