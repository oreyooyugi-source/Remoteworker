"""Tests for the screenshots app."""
from __future__ import annotations

import datetime

from django.test import TestCase
from django.utils import timezone

from apps.employees.services import create_employee_with_user
from apps.screenshots import services
from apps.screenshots.models import Screenshot


class ScreenshotTests(TestCase):
    def setUp(self):
        self.employee = create_employee_with_user(
            email="shot@example.com",
            first_name="Shot",
            last_name="Taker",
            password="Str0ng!Passw0rd",
        )

    def test_flag(self):
        shot = Screenshot.objects.create(employee=self.employee)
        shot.flag("suspicious")
        self.assertTrue(shot.is_flagged)
        self.assertEqual(shot.flag_reason, "suspicious")

    def test_timeline_groups_by_hour(self):
        Screenshot.objects.create(
            employee=self.employee, captured_at=timezone.now()
        )
        data = services.timeline(self.employee)
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["by_hour"]), 24)

    def test_purge_expired(self):
        old = Screenshot.objects.create(employee=self.employee)
        Screenshot.objects.filter(pk=old.pk).update(
            captured_at=timezone.now() - datetime.timedelta(days=200)
        )
        removed = services.purge_expired(retention_days=90)
        self.assertEqual(removed, 1)
