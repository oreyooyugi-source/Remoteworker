"""Class-based-view mixins for authentication, RBAC and convenience."""
from __future__ import annotations

from typing import Iterable

from django.contrib import messages
from django.contrib.auth.mixins import (
    AccessMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied

from apps.core import permissions as perms


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict a view to users holding one of ``allowed_roles``."""

    allowed_roles: Iterable[str] = ()
    raise_exception = True

    def test_func(self) -> bool:
        return perms.user_has_role(self.request.user, self.allowed_roles)


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict to company/super administrators."""

    raise_exception = True

    def test_func(self) -> bool:
        return perms.is_admin(self.request.user)


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict to any management role."""

    raise_exception = True

    def test_func(self) -> bool:
        return perms.is_manager(self.request.user)


class HRRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict to HR staff and administrators."""

    raise_exception = True

    def test_func(self) -> bool:
        return perms.is_hr(self.request.user)


class ModuleAccessMixin(LoginRequiredMixin, AccessMixin):
    """Restrict a view based on module-level RBAC configuration."""

    module_name: str = ""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.module_name and not perms.can_access_module(
            request.user, self.module_name
        ):
            raise PermissionDenied(
                "You do not have access to this module."
            )
        return super().dispatch(request, *args, **kwargs)


class PageTitleMixin:
    """Inject ``page_title`` / ``page_subtitle`` into the template context."""

    page_title: str = ""
    page_subtitle: str = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("page_title", self.page_title)
        context.setdefault("page_subtitle", self.page_subtitle)
        return context


class SuccessMessageMixin:
    """Flash a success message after a successful form submission."""

    success_message: str = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class AuditCreateUpdateMixin:
    """Populate ``created_by``/``updated_by`` on auditable models."""

    def form_valid(self, form):
        obj = form.save(commit=False)
        if not obj.pk and hasattr(obj, "created_by_id"):
            obj.created_by = self.request.user
        if hasattr(obj, "updated_by_id"):
            obj.updated_by = self.request.user
        obj.save()
        if hasattr(form, "save_m2m"):
            form.save_m2m()
        self.object = obj
        return super().form_valid(form)
