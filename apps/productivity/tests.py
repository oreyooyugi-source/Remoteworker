"""Tests for the productivity app."""
from __future__ import annotations

from django.test import TestCase

from apps.employees.services import create_employee_with_user
from apps.productivity import services
from apps.productivity.models import ProductivityRecord


class ProductivityTests(TestCase):
    def setUp(self):
        self.employee = create_employee_with_user(
            email="prod@example.com",
            first_name="Prod",
            last_name="Uctive",
            password="Str0ng!Passw0rd",
        )

    def test_compute_score_perfect(self):
        scores = services.compute_score(
            active_seconds=28800,
            idle_seconds=0,
            productive_seconds=28800,
            unproductive_seconds=0,
            focus_seconds=28800,
            attendance_ok=True,
        )
        self.assertEqual(scores["activity_score"], 100.0)
        self.assertGreaterEqual(scores["productivity_score"], 95)

    def test_compute_score_idle(self):
        scores = services.compute_score(
            active_seconds=3600,
            idle_seconds=3600,
            productive_seconds=1800,
            unproductive_seconds=1800,
            focus_seconds=1800,
            attendance_ok=True,
        )
        self.assertLess(scores["productivity_score"], 80)

    def test_recompute_creates_record(self):
        services.recompute_for(self.employee)
        self.assertTrue(
            ProductivityRecord.objects.filter(employee=self.employee).exists()
        )
