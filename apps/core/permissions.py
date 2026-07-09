"""Role-based access-control helpers shared across the project."""
from __future__ import annotations

from typing import Iterable

from apps.core.constants import ADMIN_ROLES, MANAGEMENT_ROLES, Role


def user_has_role(user, roles: Iterable[str]) -> bool:
    """Return ``True`` when ``user`` has one of the supplied ``roles``."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.role in set(roles)


def is_admin(user) -> bool:
    """Company or super administrators."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.role in ADMIN_ROLES


def is_manager(user) -> bool:
    """Anyone with people-management responsibilities."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.role in MANAGEMENT_ROLES


def is_hr(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.role in {Role.HR_MANAGER, *ADMIN_ROLES}


def is_auditor(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.role in {Role.AUDITOR, *ADMIN_ROLES}


def can_view_employee(user, employee) -> bool:
    """Whether ``user`` is allowed to view ``employee``'s record."""
    if not user or not user.is_authenticated:
        return False
    if is_admin(user) or is_hr(user) or is_auditor(user):
        return True
    # A user can always view their own record.
    if getattr(employee, "user_id", None) == user.id:
        return True
    # Managers can view members of their department or team.
    if is_manager(user):
        manager_employee = getattr(user, "employee_profile", None)
        if manager_employee is None:
            return False
        if (
            employee.department_id
            and employee.department_id == manager_employee.department_id
        ):
            return True
        if (
            employee.team_id
            and employee.team_id == manager_employee.team_id
        ):
            return True
    return False


def can_manage_employee(user, employee) -> bool:
    """Whether ``user`` may edit ``employee``'s record."""
    if not user or not user.is_authenticated:
        return False
    if is_admin(user) or is_hr(user):
        return True
    if is_manager(user):
        manager_employee = getattr(user, "employee_profile", None)
        if manager_employee and employee.department_id == manager_employee.department_id:
            return True
    return False


# Mapping of role -> set of module keys the role may access.
ROLE_MODULE_ACCESS: dict[str, set[str]] = {
    Role.SUPER_ADMIN: {"*"},
    Role.COMPANY_ADMIN: {"*"},
    Role.HR_MANAGER: {
        "dashboard", "employees", "attendance", "payroll", "reports",
        "analytics", "notifications", "leave", "productivity",
    },
    Role.DEPARTMENT_MANAGER: {
        "dashboard", "employees", "attendance", "projects", "tasks",
        "productivity", "monitoring", "reports", "analytics", "notifications",
    },
    Role.PROJECT_MANAGER: {
        "dashboard", "projects", "tasks", "timetracking", "reports",
        "productivity", "notifications",
    },
    Role.SUPERVISOR: {
        "dashboard", "attendance", "monitoring", "productivity", "tasks",
        "notifications",
    },
    Role.TEAM_LEAD: {
        "dashboard", "tasks", "timetracking", "productivity", "attendance",
        "notifications",
    },
    Role.EMPLOYEE: {
        "dashboard", "attendance", "timetracking", "tasks", "productivity",
        "notifications", "screenshots",
    },
    Role.AUDITOR: {
        "dashboard", "audit", "reports", "analytics", "attendance",
        "productivity", "notifications",
    },
    Role.READ_ONLY: {"dashboard", "reports", "analytics", "notifications"},
}


def can_access_module(user, module: str) -> bool:
    """Return ``True`` when ``user`` may access ``module``."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    allowed = ROLE_MODULE_ACCESS.get(user.role, set())
    return "*" in allowed or module in allowed
