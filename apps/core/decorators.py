"""Function-based-view decorators for RBAC."""
from __future__ import annotations

from functools import wraps
from typing import Iterable

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from apps.core import permissions as perms


def role_required(*roles: str):
    """Allow access only to users holding one of ``roles``."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not perms.user_has_role(request.user, roles):
                raise PermissionDenied("Insufficient role.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def module_required(module: str):
    """Allow access only to users who may access ``module``."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not perms.can_access_module(request.user, module):
                raise PermissionDenied("Module access denied.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_required(view_func):
    """Allow access only to administrators."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not perms.is_admin(request.user):
            raise PermissionDenied("Administrator access required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def ajax_required(view_func):
    """Ensure a view is only reachable via an AJAX/HTMX request."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        is_htmx = request.headers.get("HX-Request") == "true"
        if not (is_ajax or is_htmx):
            raise PermissionDenied("AJAX request required.")
        return view_func(request, *args, **kwargs)

    return _wrapped
