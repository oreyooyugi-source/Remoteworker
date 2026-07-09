"""Forms for the tasks app."""
from __future__ import annotations

from django import forms

from apps.tasks.models import Task, TaskComment

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}
_DATE = {"class": "form-control", "type": "date"}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "project",
            "milestone",
            "parent",
            "title",
            "description",
            "status",
            "priority",
            "assignees",
            "labels",
            "start_date",
            "due_date",
            "estimated_hours",
            "is_recurring",
            "recurrence",
        ]
        widgets = {
            "project": forms.Select(attrs=_SELECT),
            "milestone": forms.Select(attrs=_SELECT),
            "parent": forms.Select(attrs=_SELECT),
            "title": forms.TextInput(attrs=_TEXT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 4}),
            "status": forms.Select(attrs=_SELECT),
            "priority": forms.Select(attrs=_SELECT),
            "assignees": forms.SelectMultiple(attrs=_SELECT),
            "labels": forms.SelectMultiple(attrs=_SELECT),
            "start_date": forms.DateInput(attrs=_DATE),
            "due_date": forms.DateInput(attrs=_DATE),
            "estimated_hours": forms.NumberInput(attrs=_TEXT),
            "is_recurring": forms.CheckboxInput(attrs=_CHECK),
            "recurrence": forms.Select(attrs=_SELECT),
        }


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Write a comment…"}
            ),
        }


class ChecklistItemForm(forms.Form):
    text = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Add checklist item…"}
        )
    )
