"""Signal handlers that record authentication events in the audit log."""
from __future__ import annotations

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from apps.audit import services
from apps.audit.models import AuditAction


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs) -> None:
    services.log(
        AuditAction.LOGIN,
        actor=user,
        target=user,
        module="accounts",
        description=f"{user} signed in.",
        request=request,
    )


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs) -> None:
    if user is None:
        return
    services.log(
        AuditAction.LOGOUT,
        actor=user,
        target=user,
        module="accounts",
        description=f"{user} signed out.",
        request=request,
    )


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs) -> None:
    identifier = credentials.get("username", "unknown")
    services.log(
        AuditAction.LOGIN_FAILED,
        module="accounts",
        description=f"Failed sign-in for '{identifier}'.",
        metadata={"identifier": identifier},
        request=request,
    )
