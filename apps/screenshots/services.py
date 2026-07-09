"""Business logic for screenshot capture and thumbnails."""
from __future__ import annotations

import datetime
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils import timezone

from apps.screenshots.models import Screenshot


def generate_thumbnail(screenshot: Screenshot, size=(320, 200)) -> None:
    """Create a thumbnail (and optional blur) for a screenshot image."""
    if not screenshot.image:
        return
    try:
        from PIL import Image, ImageFilter
    except ImportError:  # pragma: no cover - Pillow optional
        return

    try:
        screenshot.image.open()
        img = Image.open(screenshot.image)
        img = img.convert("RGB")
        screenshot.width, screenshot.height = img.size

        thumb = img.copy()
        thumb.thumbnail(size)
        if screenshot.is_blurred:
            thumb = thumb.filter(ImageFilter.GaussianBlur(6))

        buffer = BytesIO()
        thumb.save(buffer, format="JPEG", quality=70, optimize=True)
        name = f"thumb_{screenshot.pk or 'new'}.jpg"
        screenshot.thumbnail.save(name, ContentFile(buffer.getvalue()), save=False)
        screenshot.file_size = screenshot.image.size
        screenshot.save(
            update_fields=["thumbnail", "width", "height", "file_size"]
        )
    except Exception:  # noqa: BLE001 - thumbnailing must not crash capture
        return


def purge_expired(retention_days: int | None = None) -> int:
    """Delete screenshots older than the retention window. Returns count."""
    from apps.settings_app.services import get_company_settings

    if retention_days is None:
        try:
            settings_obj = get_company_settings()
            retention_days = settings_obj.screenshot_interval_seconds and 90
        except Exception:  # noqa: BLE001
            retention_days = 90
    cutoff = timezone.now() - datetime.timedelta(days=retention_days or 90)
    expired = Screenshot.objects.filter(captured_at__lt=cutoff)
    count = expired.count()
    for shot in expired:
        if shot.image:
            shot.image.delete(save=False)
        if shot.thumbnail:
            shot.thumbnail.delete(save=False)
    expired.delete()
    return count


def timeline(employee, for_date=None) -> dict:
    for_date = for_date or timezone.localdate()
    shots = Screenshot.objects.filter(
        employee=employee, captured_at__date=for_date
    ).order_by("captured_at")
    # Group by hour for the timeline strip.
    by_hour: dict[int, list] = {h: [] for h in range(24)}
    for shot in shots:
        by_hour[timezone.localtime(shot.captured_at).hour].append(shot)
    return {"date": for_date, "shots": shots, "by_hour": by_hour, "count": shots.count()}
