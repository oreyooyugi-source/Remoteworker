"""Tests for the payroll app."""
from __future__ import annotations

import datetime
from decimal import Decimal

from django.test import TestCase

from apps.employees.models import SalaryInformation
from apps.employees.services import create_employee_with_user
from apps.payroll import services
from apps.payroll.models import Payslip, PayrollPeriod


class PayrollTests(TestCase):
    def setUp(self):
        self.employee = create_employee_with_user(
            email="pay@example.com",
            first_name="Pay",
            last_name="Roll",
            password="Str0ng!Passw0rd",
        )
        SalaryInformation.objects.create(
            employee=self.employee, base_salary=Decimal("5000")
        )
        self.period = PayrollPeriod.objects.create(
            name="Jan 2026",
            start_date=datetime.date(2026, 1, 1),
            end_date=datetime.date(2026, 1, 31),
        )

    def test_generate_payslip(self):
        payslip = services.generate_payslip(self.period, self.employee)
        self.assertEqual(payslip.base_salary, Decimal("5000"))
        self.assertGreater(payslip.tax_total, 0)
        self.assertLess(payslip.net_pay, payslip.gross_pay)

    def test_run_payroll(self):
        count = services.run_payroll(self.period)
        self.assertGreaterEqual(count, 1)
        self.assertTrue(Payslip.objects.filter(period=self.period).exists())

    def test_mark_period_paid(self):
        services.run_payroll(self.period)
        services.mark_period_paid(self.period)
        self.period.refresh_from_db()
        self.assertEqual(self.period.status, PayrollPeriod.Status.PAID)
