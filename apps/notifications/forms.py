"""Forms for notifications and announcements."""
from __future__ import annotations

from django import forms

from apps.notifications.models import Announcement, NotificationPreference

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        exclude = ["user", "created_at", "updated_at"]
        widgets = {
            "email_enabled": forms.CheckboxInput(attrs=_CHECK),
            "in_app_enabled": forms.CheckboxInput(attrs=_CHECK),
            "browser_enabled": forms.CheckboxInput(attrs=_CHECK),
            "notify_attendance": forms.CheckboxInput(attrs=_CHECK),
            "notify_tasks": forms.CheckboxInput(attrs=_CHECK),
            "notify_projects": forms.CheckboxInput(attrs=_CHECK),
            "notify_approvals": forms.CheckboxInput(attrs=_CHECK),
            "notify_payroll": forms.CheckboxInput(attrs=_CHECK),
            "notify_mentions": forms.CheckboxInput(attrs=_CHECK),
            "notify_announcements": forms.CheckboxInput(attrs=_CHECK),
            "digest_frequency": forms.Select(attrs=_SELECT),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "body", "priority", "department", "pinned", "expires_at"]
        widgets = {
            "title": forms.TextInput(attrs=_TEXT),
            "body": forms.Textarea(attrs={**_TEXT, "rows": 6}),
            "priority": forms.Select(attrs=_SELECT),
            "department": forms.Select(attrs=_SELECT),
            "pinned": forms.CheckboxInput(attrs=_CHECK),
            "expires_at": forms.DateTimeInput(
                attrs={**_TEXT, "type": "datetime-local"}
            ),
        }
