#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Back up the SQLite database and media directory.
# Usage: ./deploy/backup.sh [destination_dir]
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${1:-$SCRIPT_DIR/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$DEST"

echo "==> Backing up database"
if [[ -f "$SCRIPT_DIR/db.sqlite3" ]]; then
    # Use SQLite's online backup API for a consistent copy.
    sqlite3 "$SCRIPT_DIR/db.sqlite3" ".backup '$DEST/db_$STAMP.sqlite3'"
    echo "    -> $DEST/db_$STAMP.sqlite3"
fi

echo "==> Backing up media"
if [[ -d "$SCRIPT_DIR/media" ]]; then
    tar -czf "$DEST/media_$STAMP.tar.gz" -C "$SCRIPT_DIR" media
    echo "    -> $DEST/media_$STAMP.tar.gz"
fi

# Retain only the 14 most recent database backups.
ls -1t "$DEST"/db_*.sqlite3 2>/dev/null | tail -n +15 | xargs -r rm --

echo "==> Backup complete"
