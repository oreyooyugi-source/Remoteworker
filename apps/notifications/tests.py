"""Tests for the notifications app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications import services
from apps.notifications.models import Notification

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="n@example.com", username="n", password="Str0ng!Passw0rd"
        )

    def test_notify_creates_notification(self):
        note = services.notify(self.user, "Hello", "World")
        self.assertIsNotNone(note)
        self.assertEqual(Notification.objects.count(), 1)

    def test_unread_count(self):
        services.notify(self.user, "One")
        services.notify(self.user, "Two")
        self.assertEqual(services.unread_count(self.user), 2)

    def test_mark_all_read(self):
        services.notify(self.user, "One")
        services.notify(self.user, "Two")
        services.mark_all_read(self.user)
        self.assertEqual(services.unread_count(self.user), 0)

    def test_preferences_respected(self):
        prefs = services.get_preferences(self.user)
        prefs.in_app_enabled = False
        prefs.save()
        note = services.notify(self.user, "Blocked")
        self.assertIsNone(note)
