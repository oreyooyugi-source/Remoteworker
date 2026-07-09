"""Forms for the projects app."""
from __future__ import annotations

from django import forms

from apps.projects.models import Client, Milestone, Project, ProjectRisk

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}
_DATE = {"class": "form-control", "type": "date"}


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "client",
            "manager",
            "members",
            "department",
            "status",
            "priority",
            "color",
            "start_date",
            "due_date",
            "budget",
            "currency",
            "is_billable",
            "hourly_rate",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 4}),
            "client": forms.Select(attrs=_SELECT),
            "manager": forms.Select(attrs=_SELECT),
            "members": forms.SelectMultiple(attrs=_SELECT),
            "department": forms.Select(attrs=_SELECT),
            "status": forms.Select(attrs=_SELECT),
            "priority": forms.Select(attrs=_SELECT),
            "color": forms.TextInput(attrs={"class": "form-control form-control-color", "type": "color"}),
            "start_date": forms.DateInput(attrs=_DATE),
            "due_date": forms.DateInput(attrs=_DATE),
            "budget": forms.NumberInput(attrs=_TEXT),
            "currency": forms.TextInput(attrs=_TEXT),
            "is_billable": forms.CheckboxInput(attrs=_CHECK),
            "hourly_rate": forms.NumberInput(attrs=_TEXT),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "contact_name", "email", "phone", "website", "address", "logo", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "contact_name": forms.TextInput(attrs=_TEXT),
            "email": forms.EmailInput(attrs=_TEXT),
            "phone": forms.TextInput(attrs=_TEXT),
            "website": forms.URLInput(attrs=_TEXT),
            "address": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ["name", "description", "due_date", "order"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "due_date": forms.DateInput(attrs=_DATE),
            "order": forms.NumberInput(attrs=_TEXT),
        }


class ProjectRiskForm(forms.ModelForm):
    class Meta:
        model = ProjectRisk
        fields = ["title", "description", "likelihood", "impact", "mitigation"]
        widgets = {
            "title": forms.TextInput(attrs=_TEXT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "likelihood": forms.Select(attrs=_SELECT),
            "impact": forms.Select(attrs=_SELECT),
            "mitigation": forms.Textarea(attrs={**_TEXT, "rows": 2}),
        }
