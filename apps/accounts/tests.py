"""Tests for the accounts app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="jane@example.com", username="jane", password="Str0ng!Passw0rd"
        )
        self.assertEqual(user.email, "jane@example.com")
        self.assertTrue(user.check_password("Str0ng!Passw0rd"))
        self.assertFalse(user.is_staff)
        self.assertEqual(user.role, "employee")

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="root@example.com", username="root", password="Str0ng!Passw0rd"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, "super_admin")

    def test_lockout(self):
        user = User.objects.create_user(
            email="lock@example.com", username="lock", password="Str0ng!Passw0rd"
        )
        for _ in range(5):
            user.register_failed_login()
        self.assertTrue(user.is_locked)
        user.unlock_account()
        self.assertFalse(user.is_locked)

    def test_initials(self):
        user = User.objects.create_user(
            email="a@example.com", username="ab", first_name="Alice", last_name="Brown"
        )
        self.assertEqual(user.initials, "AB")


class AuthFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="bob@example.com", username="bob", password="Str0ng!Passw0rd"
        )

    def test_login_success(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "bob@example.com", "password": "Str0ng!Passw0rd"},
        )
        self.assertEqual(response.status_code, 302)

    def test_login_failure_records_attempt(self):
        from apps.accounts.models import LoginAttempt

        self.client.post(
            reverse("accounts:login"),
            {"username": "bob@example.com", "password": "wrong"},
        )
        self.assertTrue(
            LoginAttempt.objects.filter(email="bob@example.com", successful=False).exists()
        )

    def test_login_by_username(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "bob", "password": "Str0ng!Passw0rd"},
        )
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
