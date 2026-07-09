"""Admin registrations for the productivity app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.productivity.models import ProductivityGoal, ProductivityRecord


@admin.register(ProductivityRecord, site=admin_site)
class ProductivityRecordAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "productivity_score", "activity_score", "focus_score", "rating")
    list_filter = ("date",)
    search_fields = ("employee__user__first_name", "employee__user__last_name")
    date_hierarchy = "date"
    autocomplete_fields = ("employee",)


@admin.register(ProductivityGoal, site=admin_site)
class ProductivityGoalAdmin(admin.ModelAdmin):
    list_display = ("employee", "period", "target_score", "target_hours", "is_active")
    list_filter = ("period", "is_active")
