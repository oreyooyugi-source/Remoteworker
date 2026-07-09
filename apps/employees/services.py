"""Business logic for the employees app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.core.constants import Role
from apps.employees.models import Employee

User = get_user_model()


@transaction.atomic
def create_employee_with_user(
    *,
    email: str,
    first_name: str,
    last_name: str,
    role: str = Role.EMPLOYEE,
    password: str | None = None,
    department=None,
    team=None,
    job_title=None,
    **employee_kwargs,
) -> Employee:
    """Create a linked :class:`User` and :class:`Employee` atomically."""
    username = email.split("@")[0]
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        counter += 1
        username = f"{base_username}{counter}"

    user = User.objects.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
    )
    if password is None:
        user.set_unusable_password()
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])

    employee = Employee.objects.create(
        user=user,
        department=department,
        team=team,
        job_title=job_title,
        **employee_kwargs,
    )
    return employee


def org_chart(root: Employee | None = None) -> list[dict]:
    """Return a nested organisation chart starting from ``root``."""

    def build(employee: Employee) -> dict:
        return {
            "employee": employee,
            "children": [
                build(child)
                for child in employee.direct_reports.select_related("user")
            ],
        }

    if root is not None:
        return [build(root)]
    tops = Employee.objects.filter(reports_to__isnull=True).select_related("user")
    return [build(e) for e in tops]


def department_headcount() -> list[dict]:
    """Return headcount grouped by department for charts."""
    from django.db.models import Count

    from apps.employees.models import Department

    rows = (
        Department.objects.annotate(total=Count("employees"))
        .filter(is_active=True)
        .order_by("-total")
    )
    return [
        {"name": d.name, "count": d.total, "color": d.color} for d in rows
    ]
