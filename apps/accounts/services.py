"""Business logic for authentication and account management."""
from __future__ import annotations

import base64
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import (
    EmailVerificationToken,
    LoginAttempt,
    PasswordResetToken,
    UserSession,
)
from apps.core.utils import get_client_ip, get_user_agent, parse_user_agent

User = get_user_model()


def record_login_attempt(
    request, email: str, successful: bool, user=None, reason: str = ""
) -> LoginAttempt:
    """Persist a login attempt for auditing and lockout logic."""
    return LoginAttempt.objects.create(
        email=email[:254],
        user=user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        successful=successful,
        reason=reason[:128],
    )


def create_user_session(request, user) -> UserSession:
    """Create (or refresh) a :class:`UserSession` for the current request."""
    if not request.session.session_key:
        request.session.save()
    agent = get_user_agent(request)
    parsed = parse_user_agent(agent)
    session, _created = UserSession.objects.update_or_create(
        user=user,
        session_key=request.session.session_key,
        defaults={
            "ip_address": get_client_ip(request),
            "user_agent": agent,
            "device": parsed["device"],
            "browser": parsed["browser"],
            "operating_system": parsed["os"],
            "last_seen": timezone.now(),
            "is_active": True,
        },
    )
    return session


def end_user_session(request) -> None:
    """Mark the current request's :class:`UserSession` as ended."""
    key = request.session.session_key
    if not key:
        return
    UserSession.objects.filter(session_key=key, is_active=True).update(
        is_active=False, logout_at=timezone.now()
    )


def send_verification_email(request, user) -> EmailVerificationToken:
    """Issue and email an account verification link."""
    token = EmailVerificationToken.issue(user, hours=48)
    path = reverse("accounts:verify_email", kwargs={"token": token.token})
    url = request.build_absolute_uri(path)
    body = render_to_string(
        "accounts/emails/verify_email.txt",
        {"user": user, "url": url, "app_name": settings.RWT["APP_NAME"]},
    )
    send_mail(
        subject=f"Verify your {settings.RWT['APP_NAME']} account",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return token


def send_password_reset_email(request, user) -> PasswordResetToken:
    """Issue and email a password-reset link."""
    token = PasswordResetToken.issue(user, hours=2)
    path = reverse("accounts:password_reset_confirm", kwargs={"token": token.token})
    url = request.build_absolute_uri(path)
    body = render_to_string(
        "accounts/emails/password_reset.txt",
        {"user": user, "url": url, "app_name": settings.RWT["APP_NAME"]},
    )
    send_mail(
        subject=f"Reset your {settings.RWT['APP_NAME']} password",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return token


# ---------------------------------------------------------------------------
# Two-factor authentication helpers
# ---------------------------------------------------------------------------
def generate_totp_secret() -> str:
    """Return a fresh base-32 TOTP secret."""
    try:
        import pyotp

        return pyotp.random_base32()
    except ImportError:  # pragma: no cover - pyotp optional
        import secrets

        return base64.b32encode(secrets.token_bytes(20)).decode("utf-8")


def get_totp_uri(user, secret: str) -> str:
    issuer = settings.RWT["APP_NAME"].replace(" ", "")
    try:
        import pyotp

        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name=issuer
        )
    except ImportError:  # pragma: no cover
        return (
            f"otpauth://totp/{issuer}:{user.email}?secret={secret}"
            f"&issuer={issuer}"
        )


def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    try:
        import pyotp

        return pyotp.TOTP(secret).verify(code, valid_window=1)
    except ImportError:  # pragma: no cover
        return False


def totp_qr_data_uri(uri: str) -> str:
    """Return a base64 PNG data URI for a TOTP provisioning URI."""
    try:
        import qrcode

        img = qrcode.make(uri)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:  # noqa: BLE001 - qrcode optional
        return ""
