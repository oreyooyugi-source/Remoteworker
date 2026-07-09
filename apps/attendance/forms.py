"""Forms for the attendance app."""
from __future__ import annotations

from django import forms

from apps.attendance.models import (
    AttendanceCorrectionRequest,
    LeaveRequest,
    Shift,
)
from apps.settings_app.models import LeaveType

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}
_DATE = {"class": "form-control", "type": "date"}
_DATETIME = {"class": "form-control", "type": "datetime-local"}


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["leave_type", "start_date", "end_date", "half_day", "reason"]
        widgets = {
            "leave_type": forms.Select(attrs=_SELECT),
            "start_date": forms.DateInput(attrs=_DATE),
            "end_date": forms.DateInput(attrs=_DATE),
            "half_day": forms.CheckboxInput(attrs=_CHECK),
            "reason": forms.Textarea(attrs={**_TEXT, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["leave_type"].queryset = LeaveType.objects.all()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before the start date.")
        return cleaned


class CorrectionRequestForm(forms.ModelForm):
    class Meta:
        model = AttendanceCorrectionRequest
        fields = ["date", "requested_clock_in", "requested_clock_out", "reason"]
        widgets = {
            "date": forms.DateInput(attrs=_DATE),
            "requested_clock_in": forms.DateTimeInput(attrs=_DATETIME),
            "requested_clock_out": forms.DateTimeInput(attrs=_DATETIME),
            "reason": forms.Textarea(attrs={**_TEXT, "rows": 3}),
        }


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        exclude = ["created_at", "updated_at"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "shift_type": forms.Select(attrs=_SELECT),
            "start_time": forms.TimeInput(attrs={**_TEXT, "type": "time"}),
            "end_time": forms.TimeInput(attrs={**_TEXT, "type": "time"}),
            "break_minutes": forms.NumberInput(attrs=_TEXT),
            "grace_period_minutes": forms.NumberInput(attrs=_TEXT),
            "is_night_shift": forms.CheckboxInput(attrs=_CHECK),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }
