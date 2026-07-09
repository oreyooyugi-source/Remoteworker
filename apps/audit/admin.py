"""Admin registration for the audit log (read-only)."""
from __future__ import annotations

from django.contrib import admin

from apps.audit.models import AuditLog
from apps.core.admin import admin_site


@admin.register(AuditLog, site=admin_site)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor_repr", "action", "module", "target_repr", "ip_address")
    list_filter = ("action", "module", "created_at")
    search_fields = ("actor_repr", "target_repr", "description", "ip_address")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
