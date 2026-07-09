"""Reusable field and form validators."""
from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-()]{7,20}$",
    message=_("Enter a valid phone number (7-20 digits, may start with +)."),
)

# Employee code such as EMP-2024-0001
employee_code_validator = RegexValidator(
    regex=r"^[A-Z]{2,5}-[0-9]{2,4}-[0-9]{2,6}$",
    message=_("Employee code must look like EMP-2024-0001."),
)

hex_color_validator = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
    message=_("Enter a valid hex colour, e.g. #2563eb."),
)


def validate_file_size(value, max_mb: int = 10) -> None:
    """Ensure an uploaded file does not exceed ``max_mb`` megabytes."""
    limit = max_mb * 1024 * 1024
    if value.size > limit:
        raise ValidationError(
            _("File too large. Maximum size is %(max)d MB.") % {"max": max_mb}
        )


def validate_image_size(value) -> None:
    """Ensure an uploaded image is not larger than 5 MB."""
    validate_file_size(value, max_mb=5)


def validate_document_size(value) -> None:
    """Ensure an uploaded document is not larger than 25 MB."""
    validate_file_size(value, max_mb=25)


def validate_strong_password(value: str) -> None:
    """Ensure a password contains mixed case, a digit and a symbol."""
    errors = []
    if len(value) < 10:
        errors.append(_("at least 10 characters"))
    if not re.search(r"[A-Z]", value):
        errors.append(_("an uppercase letter"))
    if not re.search(r"[a-z]", value):
        errors.append(_("a lowercase letter"))
    if not re.search(r"[0-9]", value):
        errors.append(_("a digit"))
    if not re.search(r"[^A-Za-z0-9]", value):
        errors.append(_("a special character"))
    if errors:
        raise ValidationError(
            _("Password must contain %(reqs)s.")
            % {"reqs": ", ".join(str(e) for e in errors)}
        )


def validate_latitude(value: float) -> None:
    if value < -90 or value > 90:
        raise ValidationError(_("Latitude must be between -90 and 90."))


def validate_longitude(value: float) -> None:
    if value < -180 or value > 180:
        raise ValidationError(_("Longitude must be between -180 and 180."))


def validate_percentage(value: float) -> None:
    if value < 0 or value > 100:
        raise ValidationError(_("Value must be between 0 and 100."))
