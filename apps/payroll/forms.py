"""Forms for the payroll app."""
from __future__ import annotations

from django import forms

from apps.payroll.models import PayComponent, PayrollPeriod

_TEXT = {"class": "form-control"}
_SELECT = {"class": "form-select"}
_DATE = {"class": "form-control", "type": "date"}


class PayrollPeriodForm(forms.ModelForm):
    class Meta:
        model = PayrollPeriod
        fields = ["name", "start_date", "end_date", "pay_date", "notes"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "start_date": forms.DateInput(attrs=_DATE),
            "end_date": forms.DateInput(attrs=_DATE),
            "pay_date": forms.DateInput(attrs=_DATE),
            "notes": forms.TextInput(attrs=_TEXT),
        }


class PayComponentForm(forms.ModelForm):
    class Meta:
        model = PayComponent
        fields = ["component_type", "category", "name", "amount", "is_taxable"]
        widgets = {
            "component_type": forms.Select(attrs=_SELECT),
            "category": forms.TextInput(attrs=_TEXT),
            "name": forms.TextInput(attrs=_TEXT),
            "amount": forms.NumberInput(attrs=_TEXT),
            "is_taxable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
