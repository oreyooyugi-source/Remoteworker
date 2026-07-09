"""Admin registration for the analytics app."""
from __future__ import annotations

from django.contrib import admin

from apps.analytics.models import KPISnapshot
from apps.core.admin import admin_site


@admin.register(KPISnapshot, site=admin_site)
class KPISnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "headcount", "present_count", "avg_productivity", "attendance_rate", "active_projects")
    date_hierarchy = "date"
