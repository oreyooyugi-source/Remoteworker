"""Models for the audit log."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    VIEW = "view", "View"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    LOGIN_FAILED = "login_failed", "Login failed"
    DOWNLOAD = "download", "Download"
    EXPORT = "export", "Export"
    IMPORT = "import", "Import"
    APPROVE = "approve", "Approve"
    REJECT = "reject", "Reject"
    PERMISSION_CHANGE = "permission_change", "Permission change"
    ROLE_CHANGE = "role_change", "Role change"
    SETTINGS_CHANGE = "settings_change", "Settings change"
    PASSWORD_CHANGE = "password_change", "Password change"


class AuditLog(models.Model):
    """An immutable record of a single auditable action."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor_repr = models.CharField(max_length=255, blank=True)
    action = models.CharField(
        max_length=32, choices=AuditAction.choices, db_index=True
    )
    module = models.CharField(max_length=64, blank=True, db_index=True)

    target_type = models.CharField(max_length=120, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)

    description = models.TextField(blank=True)
    changes = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    path = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=8, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("audit log entry")
        verbose_name_plural = _("audit log")
        indexes = [
            models.Index(fields=["action", "module"]),
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.actor_repr or 'system'} {self.action} {self.target_repr}"

    @property
    def action_color(self) -> str:
        return {
            AuditAction.CREATE: "success",
            AuditAction.UPDATE: "info",
            AuditAction.DELETE: "danger",
            AuditAction.LOGIN: "primary",
            AuditAction.LOGOUT: "secondary",
            AuditAction.LOGIN_FAILED: "danger",
            AuditAction.EXPORT: "warning",
            AuditAction.APPROVE: "success",
            AuditAction.REJECT: "danger",
        }.get(self.action, "secondary")

    def save(self, *args, **kwargs):
        # Audit records are append-only; block updates after creation.
        if self.pk is not None:
            raise ValueError("Audit log entries are immutable.")
        super().save(*args, **kwargs)
