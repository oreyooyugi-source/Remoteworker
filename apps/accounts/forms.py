"""Forms for authentication and account management."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.utils.translation import gettext_lazy as _

from apps.core.constants import Role

User = get_user_model()

TEXT_INPUT = {"class": "form-control"}
SELECT_INPUT = {"class": "form-select"}
CHECK_INPUT = {"class": "form-check-input"}


class LoginForm(forms.Form):
    """Email/username + password login form with a remember-me option."""

    username = forms.CharField(
        label=_("Email or username"),
        widget=forms.TextInput(
            attrs={
                **TEXT_INPUT,
                "placeholder": "you@company.com",
                "autofocus": True,
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                **TEXT_INPUT,
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label=_("Keep me signed in"),
        required=False,
        widget=forms.CheckboxInput(attrs=CHECK_INPUT),
    )


class TwoFactorForm(forms.Form):
    code = forms.CharField(
        label=_("Authentication code"),
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                **TEXT_INPUT,
                "placeholder": "123456",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "autofocus": True,
            }
        ),
    )


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.EmailInput(
            attrs={**TEXT_INPUT, "placeholder": "you@company.com"}
        ),
    )


class SetPasswordForm(forms.Form):
    """Set a new password (used by both reset and forced-change flows)."""

    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={**TEXT_INPUT, "autocomplete": "new-password"}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(attrs={**TEXT_INPUT, "autocomplete": "new-password"}),
        strip=False,
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        p1 = self.cleaned_data.get("new_password1")
        p2 = self.cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("The two passwords do not match."))
        password_validation.validate_password(p2, self.user)
        return p2

    def save(self) -> None:
        if self.user is None:
            return
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save()


class PasswordChangeForm(SetPasswordForm):
    old_password = forms.CharField(
        label=_("Current password"),
        widget=forms.PasswordInput(attrs={**TEXT_INPUT, "autocomplete": "current-password"}),
        strip=False,
    )

    field_order = ["old_password", "new_password1", "new_password2"]

    def clean_old_password(self):
        old = self.cleaned_data.get("old_password")
        if not self.user.check_password(old):
            raise forms.ValidationError(_("Your current password is incorrect."))
        return old


class ProfileForm(forms.ModelForm):
    """Allow a user to edit their own profile and preferences."""

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "timezone",
            "language",
            "theme",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs=TEXT_INPUT),
            "last_name": forms.TextInput(attrs=TEXT_INPUT),
            "phone": forms.TextInput(attrs=TEXT_INPUT),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "timezone": forms.TextInput(attrs=TEXT_INPUT),
            "language": forms.TextInput(attrs=TEXT_INPUT),
            "theme": forms.Select(attrs=SELECT_INPUT),
        }


class UserForm(forms.ModelForm):
    """Administrative create/update form for users."""

    password = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput(attrs={**TEXT_INPUT, "autocomplete": "new-password"}),
        help_text=_("Leave blank to keep the existing password."),
    )

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "phone",
            "is_active",
            "is_staff",
            "email_verified",
        ]
        widgets = {
            "email": forms.EmailInput(attrs=TEXT_INPUT),
            "username": forms.TextInput(attrs=TEXT_INPUT),
            "first_name": forms.TextInput(attrs=TEXT_INPUT),
            "last_name": forms.TextInput(attrs=TEXT_INPUT),
            "role": forms.Select(attrs=SELECT_INPUT),
            "phone": forms.TextInput(attrs=TEXT_INPUT),
            "is_active": forms.CheckboxInput(attrs=CHECK_INPUT),
            "is_staff": forms.CheckboxInput(attrs=CHECK_INPUT),
            "email_verified": forms.CheckboxInput(attrs=CHECK_INPUT),
        }

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get("password")
        if raw_password:
            user.set_password(raw_password)
        elif not user.pk:
            # New user with no password -> set an unusable password.
            user.set_unusable_password()
        if commit:
            user.save()
        return user
