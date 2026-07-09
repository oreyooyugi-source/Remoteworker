"""Reusable template filters and tags for the whole project."""
from __future__ import annotations

from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

from apps.core.constants import STATUS_COLORS
from apps.core.utils import format_duration as _format_duration
from apps.core.utils import humanize_bytes as _humanize_bytes

register = template.Library()


@register.filter(name="status_color")
def status_color(value) -> str:
    """Map a status string to a Bootstrap contextual colour."""
    if value is None:
        return "secondary"
    return STATUS_COLORS.get(str(value).lower(), "secondary")


@register.filter(name="status_badge")
def status_badge(value) -> str:
    """Render a coloured Bootstrap badge for a status value."""
    if value is None:
        return ""
    color = STATUS_COLORS.get(str(value).lower(), "secondary")
    label = str(value).replace("_", " ").title()
    return mark_safe(
        f'<span class="badge rounded-pill text-bg-{color}">{label}</span>'
    )


@register.filter(name="duration")
def duration(value) -> str:
    """Format a number of seconds as a human-readable duration."""
    return _format_duration(value)


@register.filter(name="filesize")
def filesize(value) -> str:
    return _humanize_bytes(value)


@register.filter(name="get_item")
def get_item(dictionary, key):
    """Look up ``key`` in ``dictionary`` from templates."""
    if hasattr(dictionary, "get"):
        return dictionary.get(key)
    try:
        return dictionary[key]
    except (KeyError, IndexError, TypeError):
        return None


@register.filter(name="percentage_of")
def percentage_of(part, whole) -> float:
    try:
        return round((float(part) / float(whole)) * 100, 1)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0.0


@register.filter(name="initials")
def initials(value) -> str:
    """Return up to two uppercase initials for a name."""
    if not value:
        return "?"
    parts = str(value).split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.filter(name="subtract")
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value


@register.filter(name="multiply")
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value


@register.simple_tag(takes_context=True)
def active_link(context, *url_names, css_class: str = "active"):
    """Return ``css_class`` when the current URL matches any of ``url_names``."""
    request = context.get("request")
    if not request:
        return ""
    current = getattr(
        getattr(request, "resolver_match", None), "view_name", None
    )
    if current in url_names:
        return css_class
    # Also match on path prefixes for included namespaces.
    for name in url_names:
        try:
            if request.path.startswith(reverse(name)):
                return css_class
        except NoReverseMatch:
            continue
    return ""


@register.simple_tag
def query_transform(request, **kwargs):
    """Return the current query string with ``kwargs`` overridden.

    Useful for pagination links that must preserve existing filters.
    """
    updated = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            updated.pop(key, None)
        else:
            updated[key] = value
    return updated.urlencode()


@register.inclusion_tag("core/partials/stat_card.html")
def stat_card(card):
    """Render a single KPI stat card."""
    return {"card": card}
