"""Views for the productivity app."""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.core.decorators import module_required
from apps.core.permissions import is_manager
from apps.core.utils import paginate
from apps.employees.models import Employee
from apps.productivity import services
from apps.productivity.models import ProductivityRecord


@login_required
@module_required("productivity")
def productivity_dashboard(request):
    employee = getattr(request.user, "employee_profile", None)
    context = {"page_title": "Productivity", "has_profile": employee is not None}

    if employee:
        today = services.recompute_for(employee)
        context.update(
            {
                "today": today,
                "trend_json": json.dumps(services.trend(employee, days=14)),
                "recent": ProductivityRecord.objects.filter(employee=employee)[:10],
            }
        )
    if is_manager(request.user):
        context["leaderboard"] = services.leaderboard()
    return render(request, "productivity/dashboard.html", context)


@login_required
@module_required("productivity")
def productivity_records(request):
    records = ProductivityRecord.objects.select_related("employee__user")
    if not is_manager(request.user):
        employee = getattr(request.user, "employee_profile", None)
        records = records.filter(employee=employee) if employee else records.none()
    elif emp_id := request.GET.get("employee"):
        records = records.filter(employee_id=emp_id)

    page = paginate(records, request.GET.get("page"), per_page=30)
    context = {
        "page_title": "Productivity Records",
        "records": page,
        "page_obj": page,
        "is_manager": is_manager(request.user),
    }
    return render(request, "productivity/records.html", context)


@login_required
@module_required("productivity")
def employee_productivity(request, pk: int):
    if not is_manager(request.user):
        employee = getattr(request.user, "employee_profile", None)
        if not employee or employee.pk != pk:
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
    employee = get_object_or_404(Employee.objects.select_related("user"), pk=pk)
    services.recompute_for(employee)
    context = {
        "page_title": f"Productivity — {employee.full_name}",
        "employee": employee,
        "trend_json": json.dumps(services.trend(employee, days=30)),
        "records": ProductivityRecord.objects.filter(employee=employee)[:30],
    }
    return render(request, "productivity/employee.html", context)


@login_required
@module_required("productivity")
def leaderboard(request):
    context = {
        "page_title": "Productivity Leaderboard",
        "leaders": services.leaderboard(limit=25, days=30),
        "period_days": 30,
    }
    return render(request, "productivity/leaderboard.html", context)
