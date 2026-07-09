"""Tests for the reports app."""
from __future__ import annotations

from django.test import TestCase

from apps.employees.services import create_employee_with_user
from apps.reports import services
from apps.reports.models import ReportType


class ReportTests(TestCase):
    def setUp(self):
        create_employee_with_user(
            email="rep@example.com",
            first_name="Rep",
            last_name="Ort",
            password="Str0ng!Passw0rd",
        )

    def test_employee_dataset(self):
        headers, rows, title = services.build_dataset(ReportType.EMPLOYEE)
        self.assertIn("Name", headers)
        self.assertEqual(len(rows), 1)

    def test_export_csv(self):
        headers, rows, title = services.build_dataset(ReportType.EMPLOYEE)
        response = services.export_csv(headers, rows, "test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_export_dispatch(self):
        response = services.export(ReportType.EMPLOYEE, "csv")
        self.assertEqual(response.status_code, 200)
