"""Admin registration for the screenshots app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.screenshots.models import Screenshot


@admin.register(Screenshot, site=admin_site)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ("employee", "captured_at", "capture_type", "active_application", "is_flagged", "is_blurred")
    list_filter = ("capture_type", "is_flagged", "is_blurred")
    search_fields = ("employee__user__first_name", "employee__user__last_name", "active_application")
    date_hierarchy = "captured_at"
    autocomplete_fields = ("employee",)
