"""Forms for the employees app."""
from __future__ import annotations

from django import forms

from apps.core.constants import EmployeeStatus
from apps.employees.models import (
    Certification,
    Department,
    Device,
    EmergencyContact,
    Employee,
    EmployeeDocument,
    JobTitle,
    Team,
)

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_CHECK = {"class": "form-check-input"}
_DATE = {"class": "form-control", "type": "date"}


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "department",
            "team",
            "job_title",
            "branch",
            "reports_to",
            "employment_type",
            "status",
            "hire_date",
            "probation_end_date",
            "is_remote",
            "date_of_birth",
            "gender",
            "marital_status",
            "nationality",
            "personal_email",
            "phone",
            "address",
            "city",
            "country",
            "hourly_rate",
            "weekly_hours",
            "skills",
        ]
        widgets = {
            "department": forms.Select(attrs=_SELECT),
            "team": forms.Select(attrs=_SELECT),
            "job_title": forms.Select(attrs=_SELECT),
            "branch": forms.Select(attrs=_SELECT),
            "reports_to": forms.Select(attrs=_SELECT),
            "employment_type": forms.Select(attrs=_SELECT),
            "status": forms.Select(attrs=_SELECT),
            "hire_date": forms.DateInput(attrs=_DATE),
            "probation_end_date": forms.DateInput(attrs=_DATE),
            "is_remote": forms.CheckboxInput(attrs=_CHECK),
            "date_of_birth": forms.DateInput(attrs=_DATE),
            "gender": forms.Select(attrs=_SELECT),
            "marital_status": forms.TextInput(attrs=_TEXT),
            "nationality": forms.TextInput(attrs=_TEXT),
            "personal_email": forms.EmailInput(attrs=_TEXT),
            "phone": forms.TextInput(attrs=_TEXT),
            "address": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "city": forms.TextInput(attrs=_TEXT),
            "country": forms.TextInput(attrs=_TEXT),
            "hourly_rate": forms.NumberInput(attrs=_TEXT),
            "weekly_hours": forms.NumberInput(attrs=_TEXT),
            "skills": forms.SelectMultiple(attrs=_SELECT),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            "name",
            "code",
            "description",
            "parent",
            "manager",
            "branch",
            "color",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "code": forms.TextInput(attrs=_TEXT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 3}),
            "parent": forms.Select(attrs=_SELECT),
            "manager": forms.Select(attrs=_SELECT),
            "branch": forms.Select(attrs=_SELECT),
            "color": forms.TextInput(attrs={"class": "form-control form-control-color", "type": "color"}),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "department", "lead", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "department": forms.Select(attrs=_SELECT),
            "lead": forms.Select(attrs=_SELECT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 3}),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }


class JobTitleForm(forms.ModelForm):
    class Meta:
        model = JobTitle
        fields = ["name", "description", "level", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "description": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "level": forms.NumberInput(attrs=_TEXT),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }


class EmergencyContactForm(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ["name", "relationship", "phone", "email", "address", "is_primary"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "relationship": forms.TextInput(attrs=_TEXT),
            "phone": forms.TextInput(attrs=_TEXT),
            "email": forms.EmailInput(attrs=_TEXT),
            "address": forms.Textarea(attrs={**_TEXT, "rows": 2}),
            "is_primary": forms.CheckboxInput(attrs=_CHECK),
        }


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ["title", "document_type", "file", "expiry_date", "notes"]
        widgets = {
            "title": forms.TextInput(attrs=_TEXT),
            "document_type": forms.Select(attrs=_SELECT),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "expiry_date": forms.DateInput(attrs=_DATE),
            "notes": forms.Textarea(attrs={**_TEXT, "rows": 2}),
        }


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = [
            "name",
            "device_type",
            "serial_number",
            "operating_system",
            "mac_address",
            "assigned_date",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "device_type": forms.Select(attrs=_SELECT),
            "serial_number": forms.TextInput(attrs=_TEXT),
            "operating_system": forms.TextInput(attrs=_TEXT),
            "mac_address": forms.TextInput(attrs=_TEXT),
            "assigned_date": forms.DateInput(attrs=_DATE),
            "is_active": forms.CheckboxInput(attrs=_CHECK),
        }


class EmployeeFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search employees…"}
        ),
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="All departments",
        widget=forms.Select(attrs=_SELECT),
    )
    status = forms.ChoiceField(
        choices=[("", "All statuses")] + list(EmployeeStatus.choices),
        required=False,
        widget=forms.Select(attrs=_SELECT),
    )
