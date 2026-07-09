"""Tests for the attendance app."""
from __future__ import annotations

from django.test import TestCase

from apps.attendance import services
from apps.attendance.models import AttendanceRecord
from apps.employees.services import create_employee_with_user


class AttendanceTests(TestCase):
    def setUp(self):
        self.employee = create_employee_with_user(
            email="clock@example.com",
            first_name="Clock",
            last_name="Worker",
            password="Str0ng!Passw0rd",
        )

    def test_clock_in_creates_record(self):
        record = services.clock_in(self.employee)
        self.assertIsNotNone(record.clock_in)
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_clock_out_sets_worked_seconds(self):
        services.clock_in(self.employee)
        record = services.clock_out(self.employee)
        self.assertIsNotNone(record.clock_out)
        self.assertGreaterEqual(record.worked_seconds, 0)

    def test_break_cycle(self):
        services.clock_in(self.employee)
        br = services.start_break(self.employee)
        self.assertIsNotNone(br)
        ended = services.end_break(self.employee)
        self.assertIsNotNone(ended.end_time)

    def test_current_status(self):
        services.clock_in(self.employee)
        status = services.current_status(self.employee)
        self.assertEqual(status["state"], "in")
