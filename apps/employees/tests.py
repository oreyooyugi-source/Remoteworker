"""Tests for the employees app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.employees.models import Department, Employee
from apps.employees.services import create_employee_with_user

User = get_user_model()


class EmployeeTests(TestCase):
    def test_employee_code_auto_assigned(self):
        employee = create_employee_with_user(
            email="worker@example.com",
            first_name="Work",
            last_name="Er",
            password="Str0ng!Passw0rd",
        )
        self.assertTrue(employee.employee_code.startswith("EMP-"))

    def test_full_name_property(self):
        employee = create_employee_with_user(
            email="anna@example.com",
            first_name="Anna",
            last_name="Smith",
            password="Str0ng!Passw0rd",
        )
        self.assertEqual(employee.full_name, "Anna Smith")

    def test_department_headcount(self):
        dept = Department.objects.create(name="Engineering", code="ENG")
        create_employee_with_user(
            email="dev@example.com",
            first_name="Dev",
            last_name="One",
            password="Str0ng!Passw0rd",
            department=dept,
        )
        self.assertEqual(dept.employee_count, 1)

    def test_search(self):
        create_employee_with_user(
            email="searchme@example.com",
            first_name="Searchable",
            last_name="Person",
            password="Str0ng!Passw0rd",
        )
        self.assertEqual(Employee.objects.search("Searchable").count(), 1)
        self.assertEqual(Employee.objects.search("nonexistent").count(), 0)
