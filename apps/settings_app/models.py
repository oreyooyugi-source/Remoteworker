"""Models for company settings and organisational policies."""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.core.validators import hex_color_validator


class SingletonModel(TimeStampedModel):
    """Abstract base ensuring only a single row ever exists."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class CompanySettings(SingletonModel):
    """Global, company-wide configuration (a singleton row)."""

    company_name = models.CharField(max_length=160, default="Acme Corporation")
    legal_name = models.CharField(max_length=200, blank=True)
    tagline = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to="branding/", blank=True, null=True)
    favicon = models.ImageField(upload_to="branding/", blank=True, null=True)

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)

    # Branding / theme
    primary_color = models.CharField(
        max_length=7, default="#2563eb", validators=[hex_color_validator]
    )
    accent_color = models.CharField(
        max_length=7, default="#7c3aed", validators=[hex_color_validator]
    )
    default_theme = models.CharField(
        max_length=10,
        choices=[("light", "Light"), ("dark", "Dark")],
        default="light",
    )

    # Localisation
    timezone = models.CharField(max_length=64, default="UTC")
    date_format = models.CharField(max_length=20, default="Y-m-d")
    currency = models.CharField(max_length=3, default="USD")
    currency_symbol = models.CharField(max_length=4, default="$")
    fiscal_year_start_month = models.PositiveSmallIntegerField(default=1)

    # Monitoring / policy toggles
    screenshots_enabled = models.BooleanField(default=True)
    screenshot_interval_seconds = models.PositiveIntegerField(default=600)
    screenshot_blur_enabled = models.BooleanField(default=True)
    activity_tracking_enabled = models.BooleanField(default=True)
    idle_threshold_seconds = models.PositiveIntegerField(default=300)
    gps_validation_enabled = models.BooleanField(default=False)

    # Security policy
    enforce_2fa = models.BooleanField(default=False)
    password_expiry_days = models.PositiveIntegerField(default=90)
    session_timeout_minutes = models.PositiveIntegerField(default=60)
    max_login_attempts = models.PositiveIntegerField(default=5)

    class Meta:
        verbose_name = "Company settings"
        verbose_name_plural = "Company settings"

    def __str__(self) -> str:
        return self.company_name


class WorkingHoursPolicy(TimeStampedModel):
    """Definition of standard working hours / shift for a group."""

    name = models.CharField(max_length=120, default="Standard Hours")
    is_default = models.BooleanField(default=False)

    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)

    start_time = models.TimeField(default="09:00")
    end_time = models.TimeField(default="17:00")
    break_minutes = models.PositiveIntegerField(default=60)
    daily_hours = models.DecimalField(max_digits=4, decimal_places=2, default=8)
    flexible = models.BooleanField(default=False)
    grace_period_minutes = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["-is_default", "name"]
        verbose_name_plural = "Working hours policies"

    def __str__(self) -> str:
        return self.name

    @property
    def working_days(self) -> list[str]:
        days = []
        for day in [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ]:
            if getattr(self, day):
                days.append(day.title())
        return days


class LeaveType(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(max_length=10, unique=True)
    days_per_year = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    carry_forward = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default="#0ea5e9")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class HolidayCalendar(TimeStampedModel):
    name = models.CharField(max_length=120, default="Company Holidays")
    year = models.PositiveIntegerField(default=timezone.now().year)
    country = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-year", "name"]
        unique_together = ("name", "year")

    def __str__(self) -> str:
        return f"{self.name} {self.year}"


class Holiday(TimeStampedModel):
    calendar = models.ForeignKey(
        HolidayCalendar, on_delete=models.CASCADE, related_name="holidays"
    )
    name = models.CharField(max_length=120)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False)

    class Meta:
        ordering = ["date"]

    def __str__(self) -> str:
        return f"{self.name} ({self.date})"


class ProductivityRule(TimeStampedModel):
    """Classify applications / websites as productive or not."""

    class Category(models.TextChoices):
        PRODUCTIVE = "productive", "Productive"
        NEUTRAL = "neutral", "Neutral"
        UNPRODUCTIVE = "unproductive", "Unproductive"

    name = models.CharField(max_length=160)
    pattern = models.CharField(
        max_length=200, help_text="Application name or website domain to match."
    )
    category = models.CharField(
        max_length=16, choices=Category.choices, default=Category.NEUTRAL
    )
    weight = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    department = models.ForeignKey(
        "employees.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="productivity_rules",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_display()})"
