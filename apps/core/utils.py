"""General-purpose utility helpers used throughout the project."""
from __future__ import annotations

import datetime
import hashlib
import secrets
from typing import Any, Iterable

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpRequest
from django.utils import timezone
from django.utils.text import slugify


def get_client_ip(request: HttpRequest) -> str:
    """Return the best-guess client IP address for a request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def get_user_agent(request: HttpRequest) -> str:
    """Return the raw user-agent string for a request."""
    return request.META.get("HTTP_USER_AGENT", "")[:512]


def parse_user_agent(user_agent: str) -> dict[str, str]:
    """Very small, dependency-free user-agent parser.

    Returns a dict with ``browser``, ``os`` and ``device`` keys. This is a
    heuristic implementation good enough for reporting purposes.
    """
    ua = (user_agent or "").lower()

    browser = "Unknown"
    for name, token in (
        ("Edge", "edg"),
        ("Opera", "opr"),
        ("Chrome", "chrome"),
        ("Firefox", "firefox"),
        ("Safari", "safari"),
        ("Internet Explorer", "msie"),
    ):
        if token in ua:
            browser = name
            break

    operating_system = "Unknown"
    for name, token in (
        ("Windows", "windows"),
        ("macOS", "mac os"),
        ("Android", "android"),
        ("iOS", "iphone"),
        ("iOS", "ipad"),
        ("Linux", "linux"),
    ):
        if token in ua:
            operating_system = name
            break

    device = "Mobile" if any(t in ua for t in ("mobile", "iphone", "android")) else "Desktop"

    return {"browser": browser, "os": operating_system, "device": device}


def paginate(queryset: Iterable[Any], page: Any, per_page: int = 25) -> Any:
    """Paginate ``queryset`` and always return a valid page object."""
    paginator = Paginator(queryset, per_page)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def format_duration(seconds: int | float | None) -> str:
    """Format a number of seconds as ``Hh Mm`` (e.g. ``7h 45m``)."""
    if not seconds:
        return "0m"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def humanize_bytes(num_bytes: int | float | None) -> str:
    """Return a human readable file size."""
    if not num_bytes:
        return "0 B"
    step = 1024.0
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(num_bytes) < step:
            return f"{num_bytes:3.1f} {unit}"
        num_bytes /= step
    return f"{num_bytes:.1f} EB"


def generate_token(length: int = 48) -> str:
    """Return a cryptographically-secure URL-safe token."""
    return secrets.token_urlsafe(length)


def generate_reference(prefix: str) -> str:
    """Generate a short human-friendly reference such as ``EMP-8F3A2C``."""
    return f"{prefix.upper()}-{secrets.token_hex(3).upper()}"


def unique_slug(model_cls, value: str, field: str = "slug") -> str:
    """Return a slug for ``value`` that is unique for ``model_cls``."""
    base = slugify(value) or "item"
    slug = base
    counter = 1
    while model_cls._default_manager.filter(**{field: slug}).exists():
        counter += 1
        slug = f"{base}-{counter}"
    return slug


def hash_string(value: str) -> str:
    """Return a stable SHA-256 hex digest for ``value``."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def daterange(start: datetime.date, end: datetime.date) -> Iterable[datetime.date]:
    """Yield each date from ``start`` to ``end`` inclusive."""
    current = start
    while current <= end:
        yield current
        current += datetime.timedelta(days=1)


def start_of_week(value: datetime.date | None = None) -> datetime.date:
    """Return the Monday of the week containing ``value``."""
    value = value or timezone.localdate()
    return value - datetime.timedelta(days=value.weekday())


def start_of_month(value: datetime.date | None = None) -> datetime.date:
    """Return the first day of the month containing ``value``."""
    value = value or timezone.localdate()
    return value.replace(day=1)


def percentage(part: float, whole: float) -> float:
    """Return ``part`` as a percentage of ``whole`` (0 when whole is 0)."""
    if not whole:
        return 0.0
    return round((part / whole) * 100, 2)
