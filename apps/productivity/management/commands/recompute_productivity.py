"""Recompute daily productivity scorecards for all employees."""
from __future__ import annotations

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.employees.models import Employee
from apps.productivity.services import recompute_for


class Command(BaseCommand):
    help = "Rebuild productivity records from monitoring data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Number of past days to recompute (default: 1 = today).",
        )

    def handle(self, *args, **options):
        days = options["days"]
        today = timezone.localdate()
        count = 0
        employees = Employee.objects.all()
        for offset in range(days):
            day = today - datetime.timedelta(days=offset)
            for employee in employees:
                recompute_for(employee, for_date=day)
                count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Recomputed {count} productivity record(s).")
        )
