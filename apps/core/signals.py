"""Core signal handlers.

Signals that are truly cross-cutting live here. App-specific signals live
in each application's ``signals.py`` module.
"""
from __future__ import annotations

import logging

from django.db.backends.signals import connection_created
from django.dispatch import receiver

logger = logging.getLogger("rwt")


@receiver(connection_created)
def configure_sqlite(sender, connection, **kwargs) -> None:
    """Enable WAL journalling and foreign-key enforcement for SQLite.

    WAL mode is only applied to on-disk databases — it is unsupported on the
    in-memory database Django uses for the test suite and would otherwise raise
    inside the surrounding test transaction.
    """
    if connection.vendor != "sqlite":
        return
    name = str(connection.settings_dict.get("NAME", ""))
    is_memory = (":memory:" in name) or ("mode=memory" in name) or (name == "")
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    if not is_memory:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
