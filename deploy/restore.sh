#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Restore the SQLite database (and optionally media) from a backup.
# Usage: ./deploy/restore.sh <db_backup.sqlite3> [media_backup.tar.gz]
# ---------------------------------------------------------------------------
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <db_backup.sqlite3> [media_backup.tar.gz]" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_BACKUP="$1"
MEDIA_BACKUP="${2:-}"

if [[ ! -f "$DB_BACKUP" ]]; then
    echo "Database backup '$DB_BACKUP' not found." >&2
    exit 1
fi

read -r -p "This will OVERWRITE the current database. Continue? [y/N] " confirm
if [[ "${confirm,,}" != "y" ]]; then
    echo "Aborted."
    exit 0
fi

echo "==> Restoring database"
cp "$DB_BACKUP" "$SCRIPT_DIR/db.sqlite3"

if [[ -n "$MEDIA_BACKUP" && -f "$MEDIA_BACKUP" ]]; then
    echo "==> Restoring media"
    rm -rf "$SCRIPT_DIR/media"
    tar -xzf "$MEDIA_BACKUP" -C "$SCRIPT_DIR"
fi

echo "==> Restore complete. Run migrations to be safe:"
echo "    python manage.py migrate"
