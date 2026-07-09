"""Admin registrations for the monitoring app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.monitoring.models import (
    ActivitySession,
    ActivitySnapshot,
    ApplicationUsage,
    DeviceMetric,
    WebsiteUsage,
)


@admin.register(ActivitySession, site=admin_site)
class ActivitySessionAdmin(admin.ModelAdmin):
    list_display = ("employee", "started_at", "ended_at", "active_seconds", "idle_seconds", "activity_ratio", "is_active")
    list_filter = ("is_active", "operating_system", "is_vpn")
    search_fields = ("employee__user__first_name", "employee__user__last_name", "hostname")
    date_hierarchy = "started_at"
    autocomplete_fields = ("employee",)


@admin.register(ApplicationUsage, site=admin_site)
class ApplicationUsageAdmin(admin.ModelAdmin):
    list_display = ("application", "employee", "date", "category", "hours")
    list_filter = ("category", "date")
    search_fields = ("application",)


@admin.register(WebsiteUsage, site=admin_site)
class WebsiteUsageAdmin(admin.ModelAdmin):
    list_display = ("domain", "employee", "date", "category", "hours", "visits")
    list_filter = ("category", "date")
    search_fields = ("domain",)


@admin.register(DeviceMetric, site=admin_site)
class DeviceMetricAdmin(admin.ModelAdmin):
    list_display = ("employee", "captured_at", "cpu_percent", "ram_percent", "battery_percent")
    list_filter = ("network_status",)
    date_hierarchy = "captured_at"


admin_site.register(ActivitySnapshot)
