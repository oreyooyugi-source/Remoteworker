"""Tests for the audit app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.audit import services
from apps.audit.models import AuditAction, AuditLog

User = get_user_model()


class AuditTests(TestCase):
    def test_log_action(self):
        user = User.objects.create_user(
            email="a@example.com", username="a", password="Str0ng!Passw0rd"
        )
        entry = services.log(AuditAction.CREATE, actor=user, target=user, module="test")
        self.assertIsNotNone(entry)
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(entry.action, AuditAction.CREATE)

    def test_audit_log_is_immutable(self):
        entry = services.log(AuditAction.VIEW, module="test")
        with self.assertRaises(ValueError):
            entry.description = "changed"
            entry.save()

    def test_model_diff(self):
        user = User.objects.create_user(
            email="b@example.com", username="b", password="Str0ng!Passw0rd"
        )
        before = User.objects.get(pk=user.pk)
        user.first_name = "Changed"
        diff = services.model_diff(user, before)
        self.assertIn("first_name", diff)
