"""Admin registrations for the attendance app."""
from __future__ import annotations

from django.contrib import admin

from apps.attendance.models import (
    AttendanceCorrectionRequest,
    AttendanceRecord,
    BreakRecord,
    LeaveRequest,
    Shift,
)
from apps.core.admin import admin_site


class BreakInline(admin.TabularInline):
    model = BreakRecord
    extra = 0


@admin.register(AttendanceRecord, site=admin_site)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "clock_in", "clock_out", "worked_hours", "is_late")
    list_filter = ("status", "is_late", "is_early_departure", "date")
    search_fields = ("employee__user__first_name", "employee__user__last_name", "employee__employee_code")
    date_hierarchy = "date"
    inlines = [BreakInline]
    autocomplete_fields = ("employee", "shift")


@admin.register(LeaveRequest, site=admin_site)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "days", "status")
    list_filter = ("status", "leave_type")
    search_fields = ("employee__user__first_name", "employee__user__last_name")
    date_hierarchy = "start_date"
    autocomplete_fields = ("employee",)


@admin.register(Shift, site=admin_site)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("name", "shift_type", "start_time", "end_time", "expected_hours", "is_active")
    list_filter = ("shift_type", "is_active", "is_night_shift")
    search_fields = ("name",)


@admin.register(AttendanceCorrectionRequest, site=admin_site)
class CorrectionAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "created_at")
    list_filter = ("status",)


admin_site.register(BreakRecord)
