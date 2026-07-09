"""Create a timestamped backup of the database and media files."""
from __future__ import annotations

import datetime
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Back up the SQLite database and media directory to backups/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default=None,
            help="Destination directory (default: <BASE_DIR>/backups).",
        )
        parser.add_argument(
            "--no-media",
            action="store_true",
            help="Skip copying the media directory.",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        out_dir = Path(options["output"]) if options["output"] else base_dir / "backups"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # 1. Copy the SQLite database file if present.
        db_path = Path(settings.DATABASES["default"]["NAME"])
        if db_path.exists():
            dest = out_dir / f"db_{stamp}.sqlite3"
            shutil.copy2(db_path, dest)
            self.stdout.write(self.style.SUCCESS(f"Database -> {dest}"))

        # 2. Also produce a portable JSON fixture dump.
        json_path = out_dir / f"dump_{stamp}.json"
        with open(json_path, "w", encoding="utf-8") as handle:
            call_command(
                "dumpdata",
                exclude=["contenttypes", "auth.permission", "sessions.session"],
                natural_foreign=True,
                indent=2,
                stdout=handle,
            )
        self.stdout.write(self.style.SUCCESS(f"JSON dump -> {json_path}"))

        # 3. Archive the media directory.
        if not options["no_media"]:
            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists() and any(media_root.iterdir()):
                archive = out_dir / f"media_{stamp}"
                shutil.make_archive(str(archive), "zip", str(media_root))
                self.stdout.write(self.style.SUCCESS(f"Media -> {archive}.zip"))

        self.stdout.write(self.style.SUCCESS("Backup complete."))
