"""Admin registration for the reports app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.reports.models import Report


@admin.register(Report, site=admin_site)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("name", "report_type", "export_format", "generated_by", "row_count", "status", "created_at")
    list_filter = ("report_type", "export_format", "status")
    search_fields = ("name",)
    date_hierarchy = "created_at"
