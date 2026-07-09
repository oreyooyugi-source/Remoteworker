"""Managers and querysets for the employees app."""
from __future__ import annotations

from django.db import models
from django.db.models import Q

from apps.core.constants import EmployeeStatus, OnlineStatus


class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=EmployeeStatus.ACTIVE)

    def online(self):
        return self.filter(online_status=OnlineStatus.ONLINE)

    def in_department(self, department):
        return self.filter(department=department)

    def search(self, term: str):
        if not term:
            return self
        return self.filter(
            Q(user__first_name__icontains=term)
            | Q(user__last_name__icontains=term)
            | Q(user__email__icontains=term)
            | Q(employee_code__icontains=term)
            | Q(job_title__name__icontains=term)
            | Q(department__name__icontains=term)
        )


class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db).select_related(
            "user", "department", "team", "job_title", "branch"
        )

    def active(self):
        return self.get_queryset().active()

    def online(self):
        return self.get_queryset().online()

    def search(self, term: str):
        return self.get_queryset().search(term)
