"""Views for the screenshots app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.decorators import module_required
from apps.core.permissions import is_manager
from apps.core.utils import paginate
from apps.employees.models import Employee
from apps.screenshots import services
from apps.screenshots.models import Screenshot


@login_required
@module_required("screenshots")
def screenshot_list(request):
    shots = Screenshot.objects.select_related("employee__user")

    if not is_manager(request.user):
        employee = getattr(request.user, "employee_profile", None)
        shots = shots.filter(employee=employee) if employee else shots.none()
    elif emp_id := request.GET.get("employee"):
        shots = shots.filter(employee_id=emp_id)

    if flagged := request.GET.get("flagged"):
        if flagged == "1":
            shots = shots.filter(is_flagged=True)

    page = paginate(shots, request.GET.get("page"), per_page=24)
    context = {
        "page_title": "Screenshots",
        "screenshots": page,
        "page_obj": page,
        "is_manager": is_manager(request.user),
        "employees": Employee.objects.select_related("user")[:200]
        if is_manager(request.user)
        else [],
    }
    return render(request, "screenshots/list.html", context)


@login_required
@module_required("screenshots")
def screenshot_timeline(request):
    employee = getattr(request.user, "employee_profile", None)
    if is_manager(request.user) and (emp_id := request.GET.get("employee")):
        employee = get_object_or_404(Employee, pk=emp_id)
    if not employee:
        messages.info(request, "Select an employee to view their timeline.")
        return redirect("screenshots:list")

    for_date = timezone.localdate()
    if date_str := request.GET.get("date"):
        try:
            for_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    data = services.timeline(employee, for_date)
    context = {
        "page_title": f"Timeline — {employee.full_name}",
        "employee": employee,
        "timeline": data,
        "selected_date": for_date,
    }
    return render(request, "screenshots/timeline.html", context)


@login_required
@module_required("screenshots")
def screenshot_detail(request, pk: int):
    shot = get_object_or_404(Screenshot.objects.select_related("employee__user"), pk=pk)
    if not is_manager(request.user):
        employee = getattr(request.user, "employee_profile", None)
        if shot.employee_id != getattr(employee, "id", None):
            messages.error(request, "You cannot view this screenshot.")
            return redirect("screenshots:list")
    return render(
        request,
        "screenshots/detail.html",
        {"page_title": "Screenshot", "screenshot": shot},
    )


@login_required
@require_POST
def screenshot_flag(request, pk: int):
    if not is_manager(request.user):
        return redirect("screenshots:list")
    shot = get_object_or_404(Screenshot, pk=pk)
    shot.flag(request.POST.get("reason", ""))
    messages.warning(request, "Screenshot flagged for review.")
    return redirect("screenshots:detail", pk=pk)


@login_required
@require_POST
def screenshot_delete(request, pk: int):
    if not is_manager(request.user):
        return redirect("screenshots:list")
    shot = get_object_or_404(Screenshot, pk=pk)
    if shot.image:
        shot.image.delete(save=False)
    if shot.thumbnail:
        shot.thumbnail.delete(save=False)
    shot.delete()
    messages.info(request, "Screenshot deleted.")
    return redirect("screenshots:list")
