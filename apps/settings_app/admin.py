"""Admin registrations for the settings app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.settings_app.models import (
    CompanySettings,
    Holiday,
    HolidayCalendar,
    LeaveType,
    ProductivityRule,
    WorkingHoursPolicy,
)


@admin.register(CompanySettings, site=admin_site)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "currency", "timezone", "screenshots_enabled")

    def has_add_permission(self, request):
        return not CompanySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkingHoursPolicy, site=admin_site)
class WorkingHoursPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_default", "start_time", "end_time", "daily_hours", "flexible")
    list_filter = ("is_default", "flexible")


@admin.register(LeaveType, site=admin_site)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "days_per_year", "is_paid", "requires_approval")
    list_filter = ("is_paid", "requires_approval")


class HolidayInline(admin.TabularInline):
    model = Holiday
    extra = 1


@admin.register(HolidayCalendar, site=admin_site)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "country", "is_active")
    list_filter = ("year", "is_active")
    inlines = [HolidayInline]


@admin.register(ProductivityRule, site=admin_site)
class ProductivityRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "pattern", "category", "weight", "department", "is_active")
    list_filter = ("category", "is_active", "department")
    search_fields = ("name", "pattern")
