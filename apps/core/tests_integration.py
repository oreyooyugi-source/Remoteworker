"""Integration tests: authentication, RBAC and end-to-end page rendering."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.constants import Role
from apps.employees.services import create_employee_with_user

User = get_user_model()

PASSWORD = "Str0ng!Passw0rd"

# Use cookie-based sessions for these tests so ``force_login`` does not hit the
# database session table (which interacts awkwardly with
# ``SESSION_SAVE_EVERY_REQUEST`` under the test client).
cookie_sessions = override_settings(
    SESSION_ENGINE="django.contrib.sessions.backends.signed_cookies"
)


@cookie_sessions
class RBACIntegrationTests(TestCase):
    """Verify that module access is enforced per role."""

    @classmethod
    def setUpTestData(cls):
        cls.employee = create_employee_with_user(
            email="emp@example.com", first_name="Emp", last_name="Loyee",
            password=PASSWORD, role=Role.EMPLOYEE,
        )
        cls.hr = create_employee_with_user(
            email="hr@example.com", first_name="Ha", last_name="Ares",
            password=PASSWORD, role=Role.HR_MANAGER,
        )
        cls.admin = User.objects.create_superuser(
            email="root@example.com", username="root", password=PASSWORD,
        )

    def test_dashboard_accessible_to_all_authenticated(self):
        for user in (self.employee.user, self.hr.user, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse("core:dashboard")).status_code, 200)

    def test_employee_denied_restricted_modules(self):
        self.client.force_login(self.employee.user)
        for name in ["employees:list", "payroll:dashboard", "audit:list", "analytics:dashboard"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_employee_allowed_own_modules(self):
        self.client.force_login(self.employee.user)
        for name in ["attendance:dashboard", "timetracking:dashboard",
                     "productivity:dashboard", "tasks:board"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_hr_can_access_employees_and_payroll(self):
        self.client.force_login(self.hr.user)
        self.assertEqual(self.client.get(reverse("employees:list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("payroll:dashboard")).status_code, 200)

    def test_admin_can_access_everything(self):
        self.client.force_login(self.admin)
        for name in ["employees:list", "payroll:dashboard", "audit:list",
                     "analytics:dashboard", "settings_app:index", "monitoring:live"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


@cookie_sessions
class AttendanceWorkflowTests(TestCase):
    """Exercise the clock-in/out workflow through the view layer."""

    def setUp(self):
        self.employee = create_employee_with_user(
            email="worker@example.com", first_name="W", last_name="Orker",
            password=PASSWORD,
        )
        self.client.force_login(self.employee.user)

    def test_clock_in_then_out(self):
        clock_url = reverse("attendance:clock_action")
        r1 = self.client.post(clock_url, {"action": "clock_in"},
                              HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["state"], "in")

        r2 = self.client.post(clock_url, {"action": "clock_out"},
                              HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["state"], "done")


@cookie_sessions
class ReportExportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="root@example.com", username="root", password=PASSWORD,
        )
        self.client.force_login(self.admin)

    def test_csv_export_downloads(self):
        response = self.client.post(
            reverse("reports:generate"),
            {"report_type": "employee", "export_format": "csv"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])


class HealthCheckTests(TestCase):
    def test_healthz(self):
        response = self.client.get(reverse("health-check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
