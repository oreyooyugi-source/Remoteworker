"""Audit logging service functions."""
from __future__ import annotations

from typing import Any

from apps.audit.models import AuditAction, AuditLog
from apps.audit.threadlocals import get_current_request, get_current_user
from apps.core.utils import get_client_ip, get_user_agent


def log(
    action: str,
    *,
    actor=None,
    target: Any = None,
    module: str = "",
    description: str = "",
    changes: dict | None = None,
    metadata: dict | None = None,
    request=None,
) -> AuditLog | None:
    """Create an :class:`AuditLog` entry.

    Missing ``actor``/``request`` values are pulled from thread-local
    state so callers usually only need to supply the ``action`` and
    ``target``.
    """
    request = request or get_current_request()
    actor = actor or get_current_user()

    target_type = ""
    target_id = ""
    target_repr = ""
    if target is not None:
        target_type = f"{target._meta.app_label}.{target._meta.model_name}"
        target_id = str(getattr(target, "pk", ""))
        target_repr = str(target)[:255]

    ip = None
    user_agent = ""
    path = ""
    method = ""
    if request is not None:
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        path = (getattr(request, "path", "") or "")[:255]
        method = getattr(request, "method", "") or ""

    try:
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "pk", None) else None,
            actor_repr=str(actor) if actor else "system",
            action=action,
            module=module,
            target_type=target_type,
            target_id=target_id,
            target_repr=target_repr,
            description=description[:2000],
            changes=changes or {},
            metadata=metadata or {},
            ip_address=ip,
            user_agent=user_agent,
            path=path,
            method=method,
        )
    except Exception:  # noqa: BLE001 - auditing must never break the request
        return None


def log_create(target, **kwargs) -> AuditLog | None:
    return log(AuditAction.CREATE, target=target, **kwargs)


def log_update(target, changes=None, **kwargs) -> AuditLog | None:
    return log(AuditAction.UPDATE, target=target, changes=changes, **kwargs)


def log_delete(target, **kwargs) -> AuditLog | None:
    return log(AuditAction.DELETE, target=target, **kwargs)


def model_diff(instance, previous) -> dict:
    """Return a dict of changed fields between two model instances."""
    changes: dict[str, dict[str, Any]] = {}
    if previous is None:
        return changes
    for field in instance._meta.fields:
        name = field.name
        old = getattr(previous, name, None)
        new = getattr(instance, name, None)
        if old != new:
            changes[name] = {"from": _serialize(old), "to": _serialize(new)}
    return changes


def _serialize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
