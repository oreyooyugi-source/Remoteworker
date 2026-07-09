"""Views for the settings app."""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.mixins import AdminRequiredMixin  # noqa: F401 (exported)
from apps.core.permissions import is_admin
from apps.settings_app import services
from apps.settings_app.forms import (
    CompanySettingsForm,
    HolidayCalendarForm,
    LeaveTypeForm,
    ProductivityRuleForm,
    WorkingHoursPolicyForm,
)
from apps.settings_app.models import (
    HolidayCalendar,
    LeaveType,
    ProductivityRule,
    WorkingHoursPolicy,
)
from django.contrib.auth.decorators import login_required, user_passes_test

admin_only = user_passes_test(is_admin)


@login_required
@admin_only
def settings_index(request):
    context = {
        "page_title": "Settings",
        "page_subtitle": "Configure your organisation",
        "company": services.get_company_settings(),
        "policies": WorkingHoursPolicy.objects.all(),
        "leave_types": LeaveType.objects.all(),
        "rules_count": ProductivityRule.objects.count(),
        "calendars": HolidayCalendar.objects.all(),
    }
    return render(request, "settings/index.html", context)


@login_required
@admin_only
def company_settings_view(request):
    company = services.get_company_settings()
    form = CompanySettingsForm(
        request.POST or None, request.FILES or None, instance=company
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        services.invalidate_company_settings()
        messages.success(request, "Company settings updated.")
        return redirect("settings_app:company")
    return render(
        request,
        "settings/company.html",
        {"page_title": "Company Settings", "form": form},
    )


@login_required
@admin_only
def working_hours_list(request):
    policies = WorkingHoursPolicy.objects.all()
    return render(
        request,
        "settings/working_hours.html",
        {"page_title": "Working Hours", "policies": policies},
    )


@login_required
@admin_only
def working_hours_edit(request, pk: int | None = None):
    instance = get_object_or_404(WorkingHoursPolicy, pk=pk) if pk else None
    form = WorkingHoursPolicyForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Working hours policy saved.")
        return redirect("settings_app:working_hours")
    return render(
        request,
        "settings/working_hours_form.html",
        {"page_title": "Working Hours Policy", "form": form},
    )


@login_required
@admin_only
def leave_types(request):
    if request.method == "POST":
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave type added.")
            return redirect("settings_app:leave_types")
    else:
        form = LeaveTypeForm()
    return render(
        request,
        "settings/leave_types.html",
        {
            "page_title": "Leave Types",
            "leave_types": LeaveType.objects.all(),
            "form": form,
        },
    )


@login_required
@admin_only
def productivity_rules(request):
    if request.method == "POST":
        form = ProductivityRuleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Productivity rule added.")
            return redirect("settings_app:productivity_rules")
    else:
        form = ProductivityRuleForm()
    return render(
        request,
        "settings/productivity_rules.html",
        {
            "page_title": "Productivity Rules",
            "rules": ProductivityRule.objects.select_related("department"),
            "form": form,
        },
    )


@login_required
@admin_only
def holiday_calendars(request):
    if request.method == "POST":
        form = HolidayCalendarForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Holiday calendar created.")
            return redirect("settings_app:holidays")
    else:
        form = HolidayCalendarForm()
    return render(
        request,
        "settings/holidays.html",
        {
            "page_title": "Holiday Calendar",
            "calendars": HolidayCalendar.objects.prefetch_related("holidays"),
            "form": form,
        },
    )
