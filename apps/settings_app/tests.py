"""Tests for the settings app."""
from __future__ import annotations

from django.test import TestCase

from apps.settings_app.models import CompanySettings, WorkingHoursPolicy
from apps.settings_app.services import get_company_settings


class SettingsTests(TestCase):
    def test_company_settings_singleton(self):
        a = CompanySettings.load()
        b = CompanySettings.load()
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(CompanySettings.objects.count(), 1)

    def test_get_company_settings(self):
        company = get_company_settings()
        self.assertIsNotNone(company)

    def test_working_days(self):
        policy = WorkingHoursPolicy.objects.create(name="Test")
        self.assertIn("Monday", policy.working_days)
        self.assertNotIn("Sunday", policy.working_days)
