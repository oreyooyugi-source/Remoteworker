"""Signals for the tasks app."""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.audit import services as audit
from apps.tasks.models import Task


@receiver(post_save, sender=Task)
def audit_task_change(sender, instance: Task, created, **kwargs) -> None:
    action = "create" if created else "update"
    audit.log(
        action,
        target=instance,
        module="tasks",
        description=f"Task '{instance.title}' {'created' if created else 'updated'}.",
    )
