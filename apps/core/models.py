"""Abstract base models shared across all applications."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.managers import SoftDeleteManager


class TimeStampedModel(models.Model):
    """Adds self-updating ``created_at`` and ``updated_at`` fields."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(models.Model):
    """Adds a stable, non-sequential public identifier."""

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Adds soft-deletion support via ``is_deleted``/``deleted_at``."""

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(alive_only=False)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard: bool = False):
        """Soft delete by default; pass ``hard=True`` to remove permanently."""
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])
        return None

    def restore(self) -> None:
        """Undo a soft delete."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class AuditableModel(models.Model):
    """Tracks the users who created and last updated a row."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
    )

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, UUIDModel):
    """Convenience base combining timestamps and a UUID."""

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class FullBaseModel(TimeStampedModel, UUIDModel, SoftDeleteModel, AuditableModel):
    """The richest base model: timestamps, UUID, soft delete and audit."""

    class Meta:
        abstract = True
        ordering = ["-created_at"]
