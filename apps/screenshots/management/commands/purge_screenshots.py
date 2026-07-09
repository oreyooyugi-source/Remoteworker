"""Delete screenshots older than the configured retention window."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.screenshots.services import purge_expired


class Command(BaseCommand):
    help = "Delete screenshots older than the retention window."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Retention window in days (defaults to company setting / 90).",
        )

    def handle(self, *args, **options):
        removed = purge_expired(retention_days=options["days"])
        self.stdout.write(
            self.style.SUCCESS(f"Removed {removed} expired screenshot(s).")
        )
