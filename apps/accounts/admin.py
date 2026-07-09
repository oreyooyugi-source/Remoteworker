"""Admin registrations for the accounts app."""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.forms import UserForm
from apps.accounts.models import (
    CustomRole,
    EmailVerificationToken,
    LoginAttempt,
    PasswordResetToken,
    User,
    UserSession,
)
from apps.core.admin import admin_site


@admin.register(User, site=admin_site)
class UserAdmin(DjangoUserAdmin):
    add_form = UserForm
    form = UserForm
    model = User
    list_display = (
        "email",
        "get_full_name",
        "role",
        "is_active",
        "email_verified",
        "two_factor_enabled",
        "last_login",
    )
    list_filter = ("role", "is_active", "is_staff", "email_verified", "two_factor_enabled")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined", "last_activity", "last_login_ip")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone", "avatar")}),
        (_("Role & access"), {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Preferences"), {"fields": ("timezone", "language", "theme")}),
        (_("Security"), {"fields": ("email_verified", "must_change_password", "two_factor_enabled", "failed_login_attempts", "locked_until")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "last_activity", "last_login_ip")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "first_name", "last_name", "role", "password", "is_active", "is_staff"),
            },
        ),
    )


@admin.register(UserSession, site=admin_site)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "browser", "operating_system", "is_active", "login_at", "last_seen")
    list_filter = ("is_active", "browser", "operating_system")
    search_fields = ("user__email", "ip_address")
    readonly_fields = [f.name for f in UserSession._meta.fields]
    date_hierarchy = "login_at"


@admin.register(LoginAttempt, site=admin_site)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("email", "successful", "ip_address", "reason", "created_at")
    list_filter = ("successful",)
    search_fields = ("email", "ip_address")
    readonly_fields = [f.name for f in LoginAttempt._meta.fields]
    date_hierarchy = "created_at"


@admin.register(PasswordResetToken, site=admin_site)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("token",)


@admin.register(EmailVerificationToken, site=admin_site)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "used_at", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("token",)


@admin.register(CustomRole, site=admin_site)
class CustomRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "base_role", "is_active")
    list_filter = ("base_role", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
