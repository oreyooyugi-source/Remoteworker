"""Views for the monitoring app."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from apps.core.decorators import module_required
from apps.employees.models import Employee
from apps.monitoring import services


@login_required
@module_required("monitoring")
def live_dashboard(request):
    overview = services.live_overview()
    context = {
        "page_title": "Live Monitoring",
        "page_subtitle": "Real-time workforce status",
        "overview": overview,
        "counts": overview["counts"],
    }
    return render(request, "monitoring/live.html", context)


@login_required
@module_required("monitoring")
def live_data(request):
    """JSON endpoint polled by the live dashboard for auto-refresh."""
    overview = services.live_overview()
    return JsonResponse({"counts": overview["counts"]})


@login_required
@module_required("monitoring")
def employee_monitor(request, pk: int):
    employee = get_object_or_404(
        Employee.objects.select_related("user", "department"), pk=pk
    )
    activity = services.employee_activity(employee)
    context = {
        "page_title": f"Monitoring — {employee.full_name}",
        "employee": employee,
        "activity": activity,
    }
    return render(request, "monitoring/employee.html", context)


@login_required
@module_required("monitoring")
def activity_feed(request):
    from apps.monitoring.models import ActivitySession

    sessions = ActivitySession.objects.select_related(
        "employee__user"
    ).order_by("-started_at")[:50]
    context = {
        "page_title": "Activity Feed",
        "sessions": sessions,
    }
    return render(request, "monitoring/activity_feed.html", context)
