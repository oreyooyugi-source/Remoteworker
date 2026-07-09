"""
Root URL configuration for the Remote Worker Tracker System.

Each feature area lives in its own application and exposes a
namespaced URL configuration that is included below.
"""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.core.admin import admin_site
from apps.core import views as core_views

handler400 = "apps.core.views.bad_request"
handler403 = "apps.core.views.permission_denied"
handler404 = "apps.core.views.page_not_found"
handler500 = "apps.core.views.server_error"

urlpatterns = [
    # Customised admin site
    path("admin/", admin_site.urls),
    # Core / dashboards
    path("", include(("apps.core.urls", "core"), namespace="core")),
    # Authentication & account management
    path(
        "accounts/",
        include(("apps.accounts.urls", "accounts"), namespace="accounts"),
    ),
    # Feature modules
    path(
        "employees/",
        include(("apps.employees.urls", "employees"), namespace="employees"),
    ),
    path(
        "attendance/",
        include(
            ("apps.attendance.urls", "attendance"), namespace="attendance"
        ),
    ),
    path(
        "time/",
        include(
            ("apps.timetracking.urls", "timetracking"),
            namespace="timetracking",
        ),
    ),
    path(
        "monitoring/",
        include(
            ("apps.monitoring.urls", "monitoring"), namespace="monitoring"
        ),
    ),
    path(
        "screenshots/",
        include(
            ("apps.screenshots.urls", "screenshots"), namespace="screenshots"
        ),
    ),
    path(
        "productivity/",
        include(
            ("apps.productivity.urls", "productivity"),
            namespace="productivity",
        ),
    ),
    path(
        "projects/",
        include(("apps.projects.urls", "projects"), namespace="projects"),
    ),
    path(
        "tasks/",
        include(("apps.tasks.urls", "tasks"), namespace="tasks"),
    ),
    path(
        "payroll/",
        include(("apps.payroll.urls", "payroll"), namespace="payroll"),
    ),
    path(
        "notifications/",
        include(
            ("apps.notifications.urls", "notifications"),
            namespace="notifications",
        ),
    ),
    path(
        "audit/",
        include(("apps.audit.urls", "audit"), namespace="audit"),
    ),
    path(
        "reports/",
        include(("apps.reports.urls", "reports"), namespace="reports"),
    ),
    path(
        "analytics/",
        include(("apps.analytics.urls", "analytics"), namespace="analytics"),
    ),
    path(
        "settings/",
        include(
            ("apps.settings_app.urls", "settings_app"),
            namespace="settings_app",
        ),
    ),
    # Health check
    path("healthz/", core_views.health_check, name="health-check"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.BASE_DIR / "static"
    )
