"""Tests for the core application utilities and helpers."""
from __future__ import annotations

import datetime

from django.test import TestCase

from apps.core.utils import (
    format_duration,
    humanize_bytes,
    parse_user_agent,
    percentage,
    start_of_week,
)


class UtilsTests(TestCase):
    def test_format_duration(self):
        self.assertEqual(format_duration(0), "0m")
        self.assertEqual(format_duration(60), "1m")
        self.assertEqual(format_duration(3600), "1h")
        self.assertEqual(format_duration(3660), "1h 1m")
        self.assertEqual(format_duration(27900), "7h 45m")

    def test_humanize_bytes(self):
        self.assertEqual(humanize_bytes(0), "0 B")
        self.assertIn("KB", humanize_bytes(2048))
        self.assertIn("MB", humanize_bytes(5 * 1024 * 1024))

    def test_percentage(self):
        self.assertEqual(percentage(1, 4), 25.0)
        self.assertEqual(percentage(0, 0), 0.0)

    def test_parse_user_agent(self):
        chrome = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
        parsed = parse_user_agent(chrome)
        self.assertEqual(parsed["browser"], "Chrome")
        self.assertEqual(parsed["os"], "Windows")
        self.assertEqual(parsed["device"], "Desktop")

    def test_start_of_week(self):
        wednesday = datetime.date(2024, 5, 15)  # a Wednesday
        self.assertEqual(start_of_week(wednesday), datetime.date(2024, 5, 13))


class TemplateTagTests(TestCase):
    def test_status_color(self):
        from apps.core.templatetags.core_tags import status_color

        self.assertEqual(status_color("active"), "success")
        self.assertEqual(status_color("terminated"), "danger")
        self.assertEqual(status_color("unknown-value"), "secondary")
