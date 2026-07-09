"""Admin registrations for the projects app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.projects.models import Client, Milestone, Project, ProjectRisk


class MilestoneInline(admin.TabularInline):
    model = Milestone
    extra = 0


class RiskInline(admin.TabularInline):
    model = ProjectRisk
    extra = 0


@admin.register(Project, site=admin_site)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "client", "status", "priority", "progress", "due_date")
    list_filter = ("status", "priority", "is_billable")
    search_fields = ("name", "code", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("manager", "client", "department")
    filter_horizontal = ("members",)
    inlines = [MilestoneInline, RiskInline]
    date_hierarchy = "start_date"


@admin.register(Client, site=admin_site)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_name", "email", "project_count", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_name", "email")


@admin.register(Milestone, site=admin_site)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "due_date", "is_completed")
    list_filter = ("is_completed",)
    search_fields = ("name",)


@admin.register(ProjectRisk, site=admin_site)
class ProjectRiskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "likelihood", "impact", "is_resolved")
    list_filter = ("likelihood", "impact", "is_resolved")
    search_fields = ("title",)
