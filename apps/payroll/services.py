"""Business logic for payroll generation."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.payroll.models import Payslip, PayrollPeriod


def _estimate_tax(gross: Decimal) -> Decimal:
    """A simple progressive tax estimate for demonstration purposes."""
    gross = Decimal(gross)
    brackets = [
        (Decimal("1000"), Decimal("0.00")),
        (Decimal("3000"), Decimal("0.10")),
        (Decimal("6000"), Decimal("0.20")),
        (Decimal("10000"), Decimal("0.30")),
    ]
    tax = Decimal("0")
    lower = Decimal("0")
    remaining = gross
    for upper, rate in brackets:
        band = min(remaining, upper - lower)
        if band <= 0:
            break
        tax += band * rate
        remaining -= band
        lower = upper
    if remaining > 0:
        tax += remaining * Decimal("0.35")
    return tax.quantize(Decimal("0.01"))


@transaction.atomic
def generate_payslip(period: PayrollPeriod, employee) -> Payslip:
    """Create or refresh a payslip for one employee within a period."""
    salary_info = getattr(employee, "salary_information", None)
    base = Decimal(str(getattr(salary_info, "base_salary", 0) or 0))

    if base == 0 and employee.hourly_rate:
        # Fall back to hours * hourly rate for the period.
        base = _hours_for_period(period, employee) * Decimal(str(employee.hourly_rate))

    overtime_hours, overtime_pay = _overtime_for_period(period, employee)

    payslip, _created = Payslip.objects.get_or_create(
        period=period,
        employee=employee,
        defaults={"currency": getattr(salary_info, "currency", "USD")},
    )
    payslip.base_salary = base
    payslip.overtime_hours = overtime_hours
    payslip.overtime_pay = overtime_pay
    payslip.recompute()  # sets gross from components + base
    payslip.tax_total = _estimate_tax(payslip.gross_pay)
    payslip.recompute()
    payslip.save()
    return payslip


def _hours_for_period(period: PayrollPeriod, employee) -> Decimal:
    try:
        from apps.attendance.models import AttendanceRecord

        seconds = (
            AttendanceRecord.objects.filter(
                employee=employee,
                date__gte=period.start_date,
                date__lte=period.end_date,
            ).aggregate(v=Sum("worked_seconds"))["v"]
            or 0
        )
        return Decimal(seconds) / Decimal(3600)
    except Exception:  # noqa: BLE001
        return Decimal("0")


def _overtime_for_period(period: PayrollPeriod, employee):
    try:
        from apps.attendance.models import AttendanceRecord

        seconds = (
            AttendanceRecord.objects.filter(
                employee=employee,
                date__gte=period.start_date,
                date__lte=period.end_date,
            ).aggregate(v=Sum("overtime_seconds"))["v"]
            or 0
        )
        hours = Decimal(seconds) / Decimal(3600)
        rate = Decimal(str(employee.hourly_rate or 0))
        multiplier = Decimal("1.5")
        salary_info = getattr(employee, "salary_information", None)
        if salary_info:
            multiplier = Decimal(str(salary_info.overtime_multiplier))
        return hours.quantize(Decimal("0.01")), (hours * rate * multiplier).quantize(
            Decimal("0.01")
        )
    except Exception:  # noqa: BLE001
        return Decimal("0"), Decimal("0")


@transaction.atomic
def run_payroll(period: PayrollPeriod) -> int:
    """Generate payslips for every active employee in the period."""
    from apps.core.constants import EmployeeStatus
    from apps.employees.models import Employee

    period.status = PayrollPeriod.Status.PROCESSING
    period.save(update_fields=["status"])

    employees = Employee.objects.filter(status=EmployeeStatus.ACTIVE)
    count = 0
    for employee in employees:
        generate_payslip(period, employee)
        count += 1

    period.status = PayrollPeriod.Status.APPROVED
    period.save(update_fields=["status"])
    return count


def mark_period_paid(period: PayrollPeriod) -> None:
    period.payslips.update(status=Payslip.Status.PAID, paid_at=timezone.now())
    period.status = PayrollPeriod.Status.PAID
    period.pay_date = timezone.localdate()
    period.save(update_fields=["status", "pay_date"])
