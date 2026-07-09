"""Signal handlers for the accounts app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

User = get_user_model()


@receiver(pre_save, sender=User)
def track_password_change(sender, instance: "User", **kwargs) -> None:
    """Stamp ``last_password_change`` whenever the password hash changes."""
    if not instance.pk:
        instance.last_password_change = timezone.now()
        return
    try:
        previous = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    if previous.password != instance.password:
        instance.last_password_change = timezone.now()
        instance.must_change_password = False
