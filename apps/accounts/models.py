"""Models for authentication, users, roles and session tracking."""
from __future__ import annotations

import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.timezone import now as tz_now
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager
from apps.core.constants import Role
from apps.core.models import TimeStampedModel
from apps.core.utils import generate_token
from apps.core.validators import phone_validator


def avatar_upload_path(instance: "User", filename: str) -> str:
    return f"avatars/user_{instance.pk or 'new'}/{filename}"


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user authenticated by email address."""

    email = models.EmailField(_("email address"), unique=True, db_index=True)
    username = models.CharField(
        _("username"), max_length=150, unique=True, db_index=True
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    role = models.CharField(
        _("role"),
        max_length=32,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )
    phone = models.CharField(
        _("phone"), max_length=20, blank=True, validators=[phone_validator]
    )
    avatar = models.ImageField(
        _("avatar"), upload_to=avatar_upload_path, blank=True, null=True
    )

    # Preferences
    timezone = models.CharField(max_length=64, default="UTC")
    language = models.CharField(max_length=10, default="en-us")
    theme = models.CharField(
        max_length=10,
        choices=[("light", "Light"), ("dark", "Dark")],
        default="light",
    )

    # Status flags
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    email_verified = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)

    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True)

    # Security / lockout
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)

    # Activity
    date_joined = models.DateTimeField(_("date joined"), default=tz_now)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["first_name", "last_name"]
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self) -> str:
        return self.get_full_name() or self.email

    # -- Naming helpers ----------------------------------------------------
    def get_full_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def get_short_name(self) -> str:
        return self.first_name or self.username

    @property
    def initials(self) -> str:
        first = self.first_name[:1] if self.first_name else self.username[:1]
        last = self.last_name[:1] if self.last_name else ""
        return (first + last).upper()

    @property
    def display_role(self) -> str:
        return self.get_role_display()

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        return ""

    # -- Security helpers --------------------------------------------------
    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def lock_account(self, minutes: int | None = None) -> None:
        minutes = minutes or getattr(settings, "ACCOUNT_LOCK_MINUTES", 30)
        self.locked_until = timezone.now() + datetime.timedelta(minutes=minutes)
        self.save(update_fields=["locked_until"])

    def unlock_account(self) -> None:
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=["locked_until", "failed_login_attempts"])

    def register_failed_login(self) -> None:
        self.failed_login_attempts += 1
        max_attempts = getattr(settings, "MAX_LOGIN_ATTEMPTS", 5)
        if self.failed_login_attempts >= max_attempts:
            self.lock_account()
        self.save(update_fields=["failed_login_attempts", "locked_until"])

    def register_successful_login(self, ip: str | None = None) -> None:
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = timezone.now()
        self.last_activity = timezone.now()
        if ip:
            self.last_login_ip = ip
        self.save(
            update_fields=[
                "failed_login_attempts",
                "locked_until",
                "last_login",
                "last_activity",
                "last_login_ip",
            ]
        )

    def touch_activity(self) -> None:
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])


class UserSession(TimeStampedModel):
    """Tracks active and historical login sessions for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_sessions",
    )
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    device = models.CharField(max_length=64, blank=True)
    browser = models.CharField(max_length=64, blank=True)
    operating_system = models.CharField(max_length=64, blank=True)
    location = models.CharField(max_length=128, blank=True)
    login_at = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    logout_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-login_at"]
        verbose_name = "User session"
        verbose_name_plural = "User sessions"

    def __str__(self) -> str:
        return f"{self.user} @ {self.ip_address} ({self.login_at:%Y-%m-%d %H:%M})"

    def end(self) -> None:
        self.is_active = False
        self.logout_at = timezone.now()
        self.save(update_fields=["is_active", "logout_at"])


class LoginAttempt(TimeStampedModel):
    """Audit record of every login attempt, successful or not."""

    email = models.CharField(max_length=254, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_attempts",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    successful = models.BooleanField(default=False, db_index=True)
    reason = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Login attempt"
        verbose_name_plural = "Login attempts"

    def __str__(self) -> str:
        state = "success" if self.successful else "failure"
        return f"{self.email} — {state} ({self.created_at:%Y-%m-%d %H:%M})"


class TokenBase(TimeStampedModel):
    """Abstract single-use, time-limited token."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self) -> None:
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    @classmethod
    def issue(cls, user, hours: int = 24):
        return cls.objects.create(
            user=user,
            token=generate_token(),
            expires_at=timezone.now() + datetime.timedelta(hours=hours),
        )


class PasswordResetToken(TokenBase):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )

    class Meta(TokenBase.Meta):
        verbose_name = "Password reset token"
        verbose_name_plural = "Password reset tokens"


class EmailVerificationToken(TokenBase):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    class Meta(TokenBase.Meta):
        verbose_name = "Email verification token"
        verbose_name_plural = "Email verification tokens"


class CustomRole(TimeStampedModel):
    """A company-defined role used to extend the built-in role matrix."""

    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    base_role = models.CharField(
        max_length=32, choices=Role.choices, default=Role.EMPLOYEE
    )
    modules = models.JSONField(
        default=list,
        help_text="List of module keys this role may access.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Custom role"
        verbose_name_plural = "Custom roles"

    def __str__(self) -> str:
        return self.name
