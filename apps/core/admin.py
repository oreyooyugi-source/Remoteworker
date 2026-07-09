"""Customised Django admin site with dashboard statistics."""
from __future__ import annotations

from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _


class RWTAdminSite(AdminSite):
    """A branded admin site for the Remote Worker Tracker System."""

    site_title = _("RWT Administration")
    site_header = _("Remote Worker Tracker — Administration")
    index_title = _("System Control Panel")
    enable_nav_sidebar = True

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "insights/",
                self.admin_view(self.insights_view),
                name="insights",
            ),
        ]
        return custom + urls

    def insights_view(self, request):
        """Render an at-a-glance statistics dashboard inside the admin."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        context = {
            **self.each_context(request),
            "title": _("System Insights"),
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
        }
        # Lazily import optional models so the admin loads even mid-migration.
        try:
            from apps.employees.models import Department, Employee

            context["total_employees"] = Employee.objects.count()
            context["total_departments"] = Department.objects.count()
        except Exception:  # noqa: BLE001
            context["total_employees"] = 0
            context["total_departments"] = 0
        return TemplateResponse(request, "admin/insights.html", context)

    def each_context(self, request):
        context = super().each_context(request)
        context["site_url"] = "/"
        return context


# The single shared admin site instance used across the project.
admin_site = RWTAdminSite(name="rwt_admin")
