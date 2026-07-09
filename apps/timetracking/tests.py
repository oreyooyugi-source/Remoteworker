"""Tests for the timetracking app."""
from __future__ import annotations

import datetime

from django.test import TestCase
from django.utils import timezone

from apps.employees.services import create_employee_with_user
from apps.timetracking import services
from apps.timetracking.models import TimeEntry, Timesheet


class TimeTrackingTests(TestCase):
    def setUp(self):
        self.employee = create_employee_with_user(
            email="timer@example.com",
            first_name="Timer",
            last_name="User",
            password="Str0ng!Passw0rd",
        )

    def test_start_and_stop_timer(self):
        entry = services.start_timer(self.employee, description="Coding")
        self.assertTrue(entry.is_running)
        stopped = services.stop_timer(self.employee)
        self.assertFalse(stopped.is_running)
        self.assertIsNotNone(stopped.end_time)

    def test_only_one_running_timer(self):
        services.start_timer(self.employee, description="First")
        services.start_timer(self.employee, description="Second")
        running = TimeEntry.objects.filter(employee=self.employee, is_running=True)
        self.assertEqual(running.count(), 1)

    def test_manual_entry_attaches_timesheet(self):
        now = timezone.now()
        services.add_manual_entry(
            self.employee,
            start_time=now - datetime.timedelta(hours=2),
            end_time=now,
            description="Manual work",
        )
        self.assertEqual(Timesheet.objects.filter(employee=self.employee).count(), 1)
        timesheet = Timesheet.objects.get(employee=self.employee)
        self.assertGreater(timesheet.total_seconds, 0)
