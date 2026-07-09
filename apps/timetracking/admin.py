"""Admin registrations for the timetracking app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.timetracking.models import TimeEntry, Timesheet


@admin.register(TimeEntry, site=admin_site)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ("employee", "description", "project", "start_time", "duration_hours", "is_billable", "is_running")
    list_filter = ("is_billable", "is_manual", "is_running")
    search_fields = ("employee__user__first_name", "employee__user__last_name", "description")
    date_hierarchy = "start_time"
    autocomplete_fields = ("employee",)


@admin.register(Timesheet, site=admin_site)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "total_hours", "billable_hours", "status")
    list_filter = ("status", "period_type")
    search_fields = ("employee__user__first_name", "employee__user__last_name")
    date_hierarchy = "start_date"
    autocomplete_fields = ("employee",)
