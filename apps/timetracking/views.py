"""Views for the timetracking app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.constants import ApprovalStatus
from apps.core.decorators import module_required
from apps.core.permissions import is_manager
from apps.core.utils import paginate
from apps.timetracking import services
from apps.timetracking.forms import ManualTimeEntryForm
from apps.timetracking.models import TimeEntry, Timesheet


def _employee(request):
    return getattr(request.user, "employee_profile", None)


@login_required
@module_required("timetracking")
def timetracking_dashboard(request):
    employee = _employee(request)
    running = services.get_running_entry(employee) if employee else None
    summary = services.weekly_summary(employee) if employee else {}
    recent = (
        TimeEntry.objects.filter(employee=employee)
        .select_related("project", "task")[:10]
        if employee
        else []
    )
    context = {
        "page_title": "Time Tracking",
        "running_entry": running,
        "summary": summary,
        "recent_entries": recent,
        "has_profile": employee is not None,
    }
    return render(request, "timetracking/dashboard.html", context)


@login_required
@require_POST
def timer_control(request):
    employee = _employee(request)
    if not employee:
        return JsonResponse({"error": "No employee profile."}, status=400)

    action = request.POST.get("action")
    if action == "start":
        description = request.POST.get("description", "")
        project = None
        if pid := request.POST.get("project"):
            from apps.projects.models import Project

            project = Project.objects.filter(pk=pid).first()
        entry = services.start_timer(employee, description=description, project=project)
        payload = {
            "status": "running",
            "entry_id": entry.id,
            "start_time": entry.start_time.isoformat(),
        }
    elif action == "stop":
        entry = services.stop_timer(employee)
        payload = {
            "status": "stopped",
            "duration": entry.duration_hours if entry else 0,
        }
    else:
        return JsonResponse({"error": "Unknown action."}, status=400)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(payload)
    return redirect("timetracking:dashboard")


@login_required
@module_required("timetracking")
def entry_list(request):
    employee = _employee(request)
    entries = TimeEntry.objects.select_related("employee__user", "project", "task")
    if not is_manager(request.user) and employee:
        entries = entries.filter(employee=employee)
    page = paginate(entries, request.GET.get("page"), per_page=30)
    context = {
        "page_title": "Time Entries",
        "entries": page,
        "page_obj": page,
    }
    return render(request, "timetracking/entries.html", context)


@login_required
@module_required("timetracking")
def manual_entry(request):
    employee = _employee(request)
    if not employee:
        return redirect("timetracking:dashboard")
    form = ManualTimeEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        entry = services.add_manual_entry(
            employee,
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
            description=form.cleaned_data["description"],
            project=form.cleaned_data.get("project"),
            task=form.cleaned_data.get("task"),
            billable=form.cleaned_data["is_billable"],
        )
        messages.success(request, f"Added {entry.duration_hours}h entry.")
        return redirect("timetracking:entries")
    return render(
        request,
        "timetracking/manual_form.html",
        {"page_title": "Add Time Entry", "form": form},
    )


@login_required
@require_POST
def delete_entry(request, pk: int):
    employee = _employee(request)
    entry = get_object_or_404(TimeEntry, pk=pk, employee=employee)
    timesheet = entry.timesheet
    entry.delete()
    if timesheet:
        timesheet.recompute()
        timesheet.save(update_fields=["total_seconds", "billable_seconds"])
    messages.info(request, "Time entry deleted.")
    return redirect("timetracking:entries")


# ---------------------------------------------------------------------------
# Timesheets
# ---------------------------------------------------------------------------
@login_required
@module_required("timetracking")
def timesheet_list(request):
    employee = _employee(request)
    timesheets = Timesheet.objects.select_related("employee__user", "approver")
    if not is_manager(request.user) and employee:
        timesheets = timesheets.filter(employee=employee)
    if status := request.GET.get("status"):
        timesheets = timesheets.filter(status=status)
    page = paginate(timesheets, request.GET.get("page"), per_page=25)
    context = {
        "page_title": "Timesheets",
        "timesheets": page,
        "page_obj": page,
        "is_manager": is_manager(request.user),
        "statuses": ApprovalStatus.choices,
    }
    return render(request, "timetracking/timesheet_list.html", context)


@login_required
@module_required("timetracking")
def timesheet_detail(request, pk: int):
    timesheet = get_object_or_404(
        Timesheet.objects.select_related("employee__user"), pk=pk
    )
    context = {
        "page_title": "Timesheet",
        "timesheet": timesheet,
        "entries": timesheet.entries.select_related("project", "task"),
        "can_approve": is_manager(request.user),
    }
    return render(request, "timetracking/timesheet_detail.html", context)


@login_required
@require_POST
def timesheet_decision(request, pk: int):
    if not is_manager(request.user):
        return redirect("timetracking:timesheet_list")
    timesheet = get_object_or_404(Timesheet, pk=pk)
    decision = request.POST.get("decision")
    note = request.POST.get("note", "")
    if decision == "approve":
        timesheet.approve(request.user, note)
        messages.success(request, "Timesheet approved.")
    elif decision == "reject":
        timesheet.reject(request.user, note)
        messages.info(request, "Timesheet rejected.")
    return redirect("timetracking:timesheet_detail", pk=pk)


@login_required
@require_POST
def timesheet_submit(request, pk: int):
    employee = _employee(request)
    timesheet = get_object_or_404(Timesheet, pk=pk, employee=employee)
    timesheet.submit()
    messages.success(request, "Timesheet submitted for approval.")
    return redirect("timetracking:timesheet_detail", pk=pk)
