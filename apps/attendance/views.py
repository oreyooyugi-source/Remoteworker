"""Views for the attendance app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.attendance import services
from apps.attendance.forms import CorrectionRequestForm, LeaveRequestForm
from apps.attendance.models import (
    AttendanceRecord,
    AttendanceStatus,
    LeaveRequest,
)
from apps.core.constants import ApprovalStatus
from apps.core.decorators import module_required
from apps.core.permissions import is_manager
from apps.core.utils import paginate


def _require_employee(request):
    return getattr(request.user, "employee_profile", None)


@login_required
@module_required("attendance")
def attendance_dashboard(request):
    employee = _require_employee(request)
    status = services.current_status(employee) if employee else {"state": "out"}
    today = timezone.localdate()
    summary = (
        services.monthly_summary(employee, today.year, today.month)
        if employee
        else {}
    )
    recent = (
        AttendanceRecord.objects.filter(employee=employee).order_by("-date")[:10]
        if employee
        else []
    )
    context = {
        "page_title": "Attendance",
        "page_subtitle": today.strftime("%A, %d %B %Y"),
        "clock_status": status,
        "summary": summary,
        "recent": recent,
        "has_profile": employee is not None,
    }
    return render(request, "attendance/dashboard.html", context)


@login_required
@require_POST
def clock_action(request):
    """Handle clock in/out and break start/end from the dashboard widget."""
    employee = _require_employee(request)
    if not employee:
        return JsonResponse({"error": "No employee profile."}, status=400)

    action = request.POST.get("action")
    if action == "clock_in":
        services.clock_in(employee, request=request)
        message = "Clocked in successfully."
    elif action == "clock_out":
        services.clock_out(employee)
        message = "Clocked out successfully."
    elif action == "break_start":
        services.start_break(employee, request.POST.get("break_type", "short"))
        message = "Break started."
    elif action == "break_end":
        services.end_break(employee)
        message = "Break ended."
    else:
        return JsonResponse({"error": "Unknown action."}, status=400)

    status = services.current_status(employee)
    record = status["record"]
    payload = {
        "status": "ok",
        "message": message,
        "state": status["state"],
        "worked_hours": record.worked_hours if record else 0,
        "clock_in": record.clock_in.isoformat() if record and record.clock_in else None,
    }
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(payload)
    messages.success(request, message)
    return redirect("attendance:dashboard")


@login_required
@module_required("attendance")
def attendance_records(request):
    employee = _require_employee(request)
    records = AttendanceRecord.objects.select_related("employee__user", "shift")

    # Non-managers can only see their own records.
    if not is_manager(request.user) and employee:
        records = records.filter(employee=employee)

    if month := request.GET.get("month"):
        try:
            year_s, month_s = month.split("-")
            records = records.filter(date__year=int(year_s), date__month=int(month_s))
        except (ValueError, AttributeError):
            pass
    if status := request.GET.get("status"):
        records = records.filter(status=status)

    page = paginate(records, request.GET.get("page"), per_page=30)
    context = {
        "page_title": "Attendance Records",
        "records": page,
        "page_obj": page,
        "statuses": AttendanceStatus.choices,
        "is_manager": is_manager(request.user),
    }
    return render(request, "attendance/records.html", context)


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------
@login_required
@module_required("attendance")
def leave_list(request):
    employee = _require_employee(request)
    if is_manager(request.user):
        leaves = LeaveRequest.objects.select_related(
            "employee__user", "leave_type", "approver"
        )
    else:
        leaves = LeaveRequest.objects.filter(employee=employee).select_related(
            "leave_type", "approver"
        )

    if status := request.GET.get("status"):
        leaves = leaves.filter(status=status)

    page = paginate(leaves, request.GET.get("page"), per_page=25)
    context = {
        "page_title": "Leave Requests",
        "leaves": page,
        "page_obj": page,
        "is_manager": is_manager(request.user),
        "pending_count": LeaveRequest.objects.filter(
            status=ApprovalStatus.PENDING
        ).count(),
        "statuses": ApprovalStatus.choices,
    }
    return render(request, "attendance/leave_list.html", context)


@login_required
@module_required("attendance")
def leave_request(request):
    employee = _require_employee(request)
    if not employee:
        messages.error(request, "You need an employee profile to request leave.")
        return redirect("attendance:leave_list")

    form = LeaveRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        leave = form.save(commit=False)
        leave.employee = employee
        leave.save()
        messages.success(request, "Leave request submitted for approval.")
        return redirect("attendance:leave_list")
    return render(
        request,
        "attendance/leave_form.html",
        {"page_title": "Request Leave", "form": form},
    )


@login_required
@require_POST
def leave_decision(request, pk: int):
    if not is_manager(request.user):
        messages.error(request, "You cannot approve leave.")
        return redirect("attendance:leave_list")
    leave = get_object_or_404(LeaveRequest, pk=pk)
    decision = request.POST.get("decision")
    note = request.POST.get("note", "")
    if decision == "approve":
        leave.approve(request.user, note)
        messages.success(request, "Leave approved.")
    elif decision == "reject":
        leave.reject(request.user, note)
        messages.info(request, "Leave rejected.")
    return redirect("attendance:leave_list")


@login_required
@module_required("attendance")
def correction_request(request):
    employee = _require_employee(request)
    if not employee:
        return redirect("attendance:dashboard")
    form = CorrectionRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        correction = form.save(commit=False)
        correction.employee = employee
        correction.save()
        messages.success(request, "Correction request submitted.")
        return redirect("attendance:records")
    return render(
        request,
        "attendance/correction_form.html",
        {"page_title": "Attendance Correction", "form": form},
    )


@login_required
@module_required("attendance")
def team_attendance(request):
    """Manager view: today's attendance across the team."""
    if not is_manager(request.user):
        return redirect("attendance:dashboard")
    today = timezone.localdate()
    records = (
        AttendanceRecord.objects.filter(date=today)
        .select_related("employee__user", "employee__department")
        .order_by("employee__user__first_name")
    )
    context = {
        "page_title": "Team Attendance",
        "page_subtitle": today.strftime("%A, %d %B %Y"),
        "records": records,
        "present": records.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.REMOTE]
        ).count(),
        "late": records.filter(is_late=True).count(),
        "absent": records.filter(status=AttendanceStatus.ABSENT).count(),
    }
    return render(request, "attendance/team.html", context)
