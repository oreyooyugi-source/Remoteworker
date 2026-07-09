"""Tests for the monitoring app."""
from __future__ import annotations

from django.test import TestCase

from apps.core.constants import OnlineStatus
from apps.employees.services import create_employee_with_user
from apps.monitoring import services
from apps.monitoring.models import ActivitySession


class MonitoringTests(TestCase):
    def setUp(self):
        self.employee = create_employee_with_user(
            email="mon@example.com",
            first_name="Mon",
            last_name="Itor",
            password="Str0ng!Passw0rd",
        )

    def test_activity_ratio(self):
        session = ActivitySession.objects.create(
            employee=self.employee, active_seconds=3600, idle_seconds=1200
        )
        self.assertEqual(session.activity_ratio, 75.0)

    def test_live_overview_counts(self):
        self.employee.set_online_status(OnlineStatus.WORKING)
        overview = services.live_overview()
        self.assertGreaterEqual(overview["counts"]["working"], 1)

    def test_employee_activity_summary(self):
        ActivitySession.objects.create(
            employee=self.employee, active_seconds=7200, idle_seconds=1800
        )
        summary = services.employee_activity(self.employee)
        self.assertEqual(summary["active_hours"], 2.0)
