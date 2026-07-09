"""Forms for the settings app."""
from __future__ import annotations

from django import forms

from apps.settings_app.models import (
    CompanySettings,
    HolidayCalendar,
    LeaveType,
    ProductivityRule,
    WorkingHoursPolicy,
)

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}
_COLOR = {"class": "form-control form-control-color", "type": "color"}


class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = CompanySettings
        exclude = ["created_at", "updated_at"]
        widgets = {
            "company_name": forms.TextInput(attrs=_TEXT),
            "legal_name": forms.TextInput(attrs=_TEXT),
            "tagline": forms.TextInput(attrs=_TEXT),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "favicon": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs=_TEXT),
            "phone": forms.TextInput(attrs=_TEXT),
            "website": forms.URLInput(attrs=_TEXT),
            "address": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "primary_color": forms.TextInput(attrs=_COLOR),
            "accent_color": forms.TextInput(attrs=_COLOR),
            "default_theme": forms.Select(attrs=_SELECT),
            "timezone": forms.TextInput(attrs=_TEXT),
            "date_format": forms.TextInput(attrs=_TEXT),
            "currency": forms.TextInput(attrs=_TEXT),
            "currency_symbol": forms.TextInput(attrs=_TEXT),
            "fiscal_year_start_month": forms.NumberInput(attrs=_TEXT),
            "screenshots_enabled": forms.CheckboxInput(attrs=_CHECK),
            "screenshot_interval_seconds": forms.NumberInput(attrs=_TEXT),
            "screenshot_blur_enabled": forms.CheckboxInput(attrs=_CHECK),
            "activity_tracking_enabled": forms.CheckboxInput(attrs=_CHECK),
            "idle_threshold_seconds": forms.NumberInput(attrs=_TEXT),
            "gps_validation_enabled": forms.CheckboxInput(attrs=_CHECK),
            "enforce_2fa": forms.CheckboxInput(attrs=_CHECK),
            "password_expiry_days": forms.NumberInput(attrs=_TEXT),
            "session_timeout_minutes": forms.NumberInput(attrs=_TEXT),
            "max_login_attempts": forms.NumberInput(attrs=_TEXT),
        }


class WorkingHoursPolicyForm(forms.ModelForm):
    class Meta:
        model = WorkingHoursPolicy
        exclude = ["created_at", "updated_at"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "is_default": forms.CheckboxInput(attrs=_CHECK),
            "monday": forms.CheckboxInput(attrs=_CHECK),
            "tuesday": forms.CheckboxInput(attrs=_CHECK),
            "wednesday": forms.CheckboxInput(attrs=_CHECK),
            "thursday": forms.CheckboxInput(attrs=_CHECK),
            "friday": forms.CheckboxInput(attrs=_CHECK),
            "saturday": forms.CheckboxInput(attrs=_CHECK),
            "sunday": forms.CheckboxInput(attrs=_CHECK),
            "start_time": forms.TimeInput(attrs={**_TEXT, "type": "time"}),
            "end_time": forms.TimeInput(attrs={**_TEXT, "type": "time"}),
            "break_minutes": forms.NumberInput(attrs=_TEXT),
            "daily_hours": forms.NumberInput(attrs=_TEXT),
            "flexible": forms.CheckboxInput(attrs=_CHECK),
            "grace_period_minutes": forms.NumberInput(attrs=_TEXT),
        }


class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        exclude = ["created_at", "updated_at"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "code": forms.TextInput(attrs=_TEXT),
            "days_per_year": forms.NumberInput(attrs=_TEXT),
            "is_paid": forms.CheckboxInput(attrs=_CHECK),
            "requires_approval": forms.CheckboxInput(attrs=_CHECK),
            "carry_forward": forms.CheckboxInput(attrs=_CHECK),
            "color": forms.TextInput(attrs=_COLOR),
        }


class ProductivityRuleForm(forms.ModelForm):
    class Meta:
        model = ProductivityRule
        exclude = ["created_at", "updated_at"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "pattern": forms.TextInput(attrs=_TEXT),
            "category": forms.Select(attrs=_SELECT),
            "weight": forms.NumberInput(attrs=_TEXT),
            "department": forms.Select(attrs=_SELECT),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }


class HolidayCalendarForm(forms.ModelForm):
    class Meta:
        model = HolidayCalendar
        exclude = ["created_at", "updated_at"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "year": forms.NumberInput(attrs=_TEXT),
            "country": forms.TextInput(attrs=_TEXT),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }
