"""Reusable model managers and query sets for the core app."""
from __future__ import annotations

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that understands soft deletion semantics."""

    def alive(self) -> "SoftDeleteQuerySet":
        return self.filter(is_deleted=False)

    def dead(self) -> "SoftDeleteQuerySet":
        return self.filter(is_deleted=True)

    def delete(self):  # type: ignore[override]
        """Soft delete every row in the queryset."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently remove the rows from the database."""
        return super().delete()


class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows."""

    def __init__(self, *args, alive_only: bool = True, **kwargs) -> None:
        self.alive_only = alive_only
        super().__init__(*args, **kwargs)

    def get_queryset(self) -> SoftDeleteQuerySet:
        qs = SoftDeleteQuerySet(self.model, using=self._db)
        if self.alive_only:
            return qs.filter(is_deleted=False)
        return qs

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class ActiveQuerySet(models.QuerySet):
    """QuerySet helpers for models with an ``is_active`` flag."""

    def active(self) -> "ActiveQuerySet":
        return self.filter(is_active=True)

    def inactive(self) -> "ActiveQuerySet":
        return self.filter(is_active=False)


class ActiveManager(models.Manager):
    """Manager exposing ``active``/``inactive`` helpers."""

    def get_queryset(self) -> ActiveQuerySet:
        return ActiveQuerySet(self.model, using=self._db)

    def active(self) -> ActiveQuerySet:
        return self.get_queryset().active()

    def inactive(self) -> ActiveQuerySet:
        return self.get_queryset().inactive()
