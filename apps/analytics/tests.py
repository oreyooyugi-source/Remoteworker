"""Tests for the analytics app."""
from __future__ import annotations

from django.test import TestCase

from apps.analytics import services
from apps.employees.services import create_employee_with_user


class AnalyticsTests(TestCase):
    def setUp(self):
        create_employee_with_user(
            email="ana@example.com",
            first_name="Ana",
            last_name="Lytics",
            password="Str0ng!Passw0rd",
        )

    def test_company_kpis(self):
        kpis = services.company_kpis()
        self.assertIn("headcount", kpis)
        self.assertEqual(kpis["headcount"], 1)

    def test_headcount_by_department_shape(self):
        data = services.headcount_by_department()
        self.assertIn("labels", data)
        self.assertIn("data", data)

    def test_attendance_trend_length(self):
        trend = services.attendance_trend(7)
        self.assertEqual(len(trend["labels"]), 7)
