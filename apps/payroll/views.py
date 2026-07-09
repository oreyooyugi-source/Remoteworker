"""Views for the payroll app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.decorators import module_required
from apps.core.permissions import is_hr
from apps.core.utils import paginate
from apps.payroll import services
from apps.payroll.forms import PayrollPeriodForm
from apps.payroll.models import Payslip, PayrollPeriod

hr_only = user_passes_test(is_hr)


@login_required
@module_required("payroll")
def payroll_dashboard(request):
    employee = getattr(request.user, "employee_profile", None)
    context = {"page_title": "Payroll"}

    if is_hr(request.user):
        context.update(
            {
                "periods": PayrollPeriod.objects.all()[:12],
                "recent_payslips": Payslip.objects.select_related(
                    "employee__user", "period"
                )[:10],
                "is_hr": True,
            }
        )
    if employee:
        context["my_payslips"] = Payslip.objects.filter(
            employee=employee
        ).select_related("period")[:12]
    return render(request, "payroll/dashboard.html", context)


@login_required
@hr_only
def period_list(request):
    periods = PayrollPeriod.objects.all()
    page = paginate(periods, request.GET.get("page"), per_page=20)
    return render(
        request,
        "payroll/period_list.html",
        {"page_title": "Payroll Periods", "periods": page, "page_obj": page},
    )


@login_required
@hr_only
def period_create(request):
    form = PayrollPeriodForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        period = form.save()
        messages.success(request, f"Payroll period '{period.name}' created.")
        return redirect("payroll:period_detail", pk=period.pk)
    return render(
        request,
        "payroll/period_form.html",
        {"page_title": "New Payroll Period", "form": form},
    )


@login_required
@hr_only
def period_detail(request, pk: int):
    period = get_object_or_404(PayrollPeriod, pk=pk)
    context = {
        "page_title": period.name,
        "period": period,
        "payslips": period.payslips.select_related("employee__user"),
    }
    return render(request, "payroll/period_detail.html", context)


@login_required
@hr_only
def run_payroll(request, pk: int):
    period = get_object_or_404(PayrollPeriod, pk=pk)
    if request.method == "POST":
        count = services.run_payroll(period)
        messages.success(request, f"Generated {count} payslips.")
    return redirect("payroll:period_detail", pk=pk)


@login_required
@hr_only
def mark_paid(request, pk: int):
    period = get_object_or_404(PayrollPeriod, pk=pk)
    if request.method == "POST":
        services.mark_period_paid(period)
        messages.success(request, "Payroll marked as paid.")
    return redirect("payroll:period_detail", pk=pk)


@login_required
@module_required("payroll")
def payslip_detail(request, pk: int):
    payslip = get_object_or_404(
        Payslip.objects.select_related("employee__user", "period"), pk=pk
    )
    # Employees may only view their own payslips.
    if not is_hr(request.user):
        employee = getattr(request.user, "employee_profile", None)
        if payslip.employee_id != getattr(employee, "id", None):
            messages.error(request, "You cannot view this payslip.")
            return redirect("payroll:dashboard")
    context = {
        "page_title": f"Payslip {payslip.reference}",
        "payslip": payslip,
        "components": payslip.components.all(),
    }
    return render(request, "payroll/payslip_detail.html", context)
