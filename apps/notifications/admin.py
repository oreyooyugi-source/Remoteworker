"""Admin registrations for the notifications app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.notifications.models import (
    Announcement,
    Notification,
    NotificationPreference,
)


@admin.register(Notification, site=admin_site)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "notification_type", "priority", "is_read", "created_at")
    list_filter = ("notification_type", "priority", "is_read")
    search_fields = ("title", "message", "recipient__email")
    date_hierarchy = "created_at"


@admin.register(Announcement, site=admin_site)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "priority", "department", "is_published", "pinned", "published_at")
    list_filter = ("priority", "is_published", "pinned")
    search_fields = ("title", "body")
    date_hierarchy = "published_at"


@admin.register(NotificationPreference, site=admin_site)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_enabled", "in_app_enabled", "digest_frequency")
    list_filter = ("email_enabled", "in_app_enabled", "digest_frequency")
    search_fields = ("user__email",)
