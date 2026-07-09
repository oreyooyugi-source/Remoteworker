"""Forms for the timetracking app."""
from __future__ import annotations

from django import forms

from apps.timetracking.models import TimeEntry

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}
_DATETIME = {"class": "form-control", "type": "datetime-local"}


class ManualTimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = [
            "description",
            "project",
            "task",
            "start_time",
            "end_time",
            "is_billable",
        ]
        widgets = {
            "description": forms.TextInput(attrs=_TEXT),
            "project": forms.Select(attrs=_SELECT),
            "task": forms.Select(attrs=_SELECT),
            "start_time": forms.DateTimeInput(attrs=_DATETIME),
            "end_time": forms.DateTimeInput(attrs=_DATETIME),
            "is_billable": forms.CheckboxInput(attrs=_CHECK),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after the start time.")
        return cleaned


class TimerStartForm(forms.Form):
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "What are you working on?"}
        ),
    )
    project = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="No project",
        widget=forms.Select(attrs=_SELECT),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.projects.models import Project

        self.fields["project"].queryset = Project.objects.filter(
            status__in=["active", "planning"]
        )
