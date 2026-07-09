"""Admin registrations for the tasks app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.tasks.models import (
    ChecklistItem,
    Label,
    Task,
    TaskActivity,
    TaskAttachment,
    TaskComment,
)


class ChecklistInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0


class CommentInline(admin.StackedInline):
    model = TaskComment
    extra = 0


@admin.register(Task, site=admin_site)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "due_date", "is_overdue")
    list_filter = ("status", "priority", "is_recurring")
    search_fields = ("title", "description")
    autocomplete_fields = ("project", "milestone", "parent")
    filter_horizontal = ("assignees", "labels", "depends_on")
    inlines = [ChecklistInline, CommentInline]
    date_hierarchy = "created_at"


@admin.register(Label, site=admin_site)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(TaskActivity, site=admin_site)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ("task", "actor", "verb", "created_at")
    search_fields = ("verb", "detail")


admin_site.register(TaskComment)
admin_site.register(TaskAttachment)
admin_site.register(ChecklistItem)
