"""Views for authentication and account self-service."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.accounts import services
from apps.accounts.forms import (
    ForgotPasswordForm,
    LoginForm,
    PasswordChangeForm,
    ProfileForm,
    SetPasswordForm,
    TwoFactorForm,
)
from apps.accounts.models import (
    EmailVerificationToken,
    LoginAttempt,
    PasswordResetToken,
    UserSession,
)
from apps.core.utils import get_client_ip

User = get_user_model()


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request):
    """Authenticate a user, handling lockout and optional 2FA."""
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        remember = form.cleaned_data["remember_me"]

        # Look up the user to enforce lockout before authenticating.
        lookup = User.objects.filter(email__iexact=identifier).first() or (
            User.objects.filter(username__iexact=identifier).first()
        )
        if lookup and lookup.is_locked:
            services.record_login_attempt(
                request, identifier, False, lookup, "account_locked"
            )
            messages.error(
                request,
                "This account is temporarily locked due to repeated failed "
                "sign-in attempts. Try again later.",
            )
            return render(request, "accounts/login.html", {"form": form})

        user = authenticate(request, username=identifier, password=password)
        if user is None:
            if lookup:
                lookup.register_failed_login()
            services.record_login_attempt(
                request, identifier, False, lookup, "invalid_credentials"
            )
            messages.error(request, "Invalid credentials. Please try again.")
            return render(request, "accounts/login.html", {"form": form})

        if not user.is_active:
            services.record_login_attempt(
                request, identifier, False, user, "inactive"
            )
            messages.error(request, "Your account has been deactivated.")
            return render(request, "accounts/login.html", {"form": form})

        # Two-factor challenge, if enabled.
        if user.two_factor_enabled and user.totp_secret:
            request.session["pre_2fa_user_id"] = user.id
            request.session["pre_2fa_remember"] = remember
            return redirect("accounts:two_factor")

        return _complete_login(request, user, remember)

    return render(request, "accounts/login.html", {"form": form})


def _complete_login(request, user, remember: bool):
    """Finalise a successful authentication."""
    login(request, user)
    if not remember:
        request.session.set_expiry(0)  # expire at browser close
    user.register_successful_login(ip=get_client_ip(request))
    services.record_login_attempt(request, user.email, True, user, "ok")
    services.create_user_session(request, user)
    messages.success(request, f"Welcome back, {user.get_short_name()}!")
    if user.must_change_password:
        return redirect("accounts:password_change")
    next_url = request.GET.get("next") or request.POST.get("next")
    return redirect(next_url or "core:dashboard")


@never_cache
@require_http_methods(["GET", "POST"])
def two_factor_view(request):
    """Validate a TOTP code during the two-factor login flow."""
    user_id = request.session.get("pre_2fa_user_id")
    if not user_id:
        return redirect("accounts:login")
    user = get_object_or_404(User, pk=user_id)

    form = TwoFactorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
        if services.verify_totp(user.totp_secret, code):
            remember = request.session.pop("pre_2fa_remember", False)
            request.session.pop("pre_2fa_user_id", None)
            return _complete_login(request, user, remember)
        messages.error(request, "Invalid authentication code.")
    return render(request, "accounts/two_factor.html", {"form": form})


@login_required
def logout_view(request):
    services.end_user_session(request)
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def forgot_password_view(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            services.send_password_reset_email(request, user)
        # Always show the same message to avoid account enumeration.
        messages.success(
            request,
            "If an account exists for that email, a reset link has been sent.",
        )
        return redirect("accounts:login")
    return render(request, "accounts/forgot_password.html", {"form": form})


@require_http_methods(["GET", "POST"])
def password_reset_confirm_view(request, token: str):
    reset = PasswordResetToken.objects.filter(token=token).first()
    if not reset or not reset.is_valid:
        messages.error(request, "This reset link is invalid or has expired.")
        return redirect("accounts:forgot_password")

    form = SetPasswordForm(user=reset.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        reset.mark_used()
        messages.success(
            request, "Your password has been reset. You can now sign in."
        )
        return redirect("accounts:login")
    return render(
        request, "accounts/password_reset_confirm.html", {"form": form}
    )


def verify_email_view(request, token: str):
    verification = EmailVerificationToken.objects.filter(token=token).first()
    if not verification or not verification.is_valid:
        messages.error(
            request, "This verification link is invalid or has expired."
        )
        return redirect("accounts:login")
    user = verification.user
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    verification.mark_used()
    messages.success(request, "Your email address has been verified.")
    return redirect("accounts:login")


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    form = PasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        # Keep the user logged in after the password change.
        from django.contrib.auth import update_session_auth_hash

        update_session_auth_hash(request, request.user)
        messages.success(request, "Your password has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/password_change.html", {"form": form})


@login_required
def profile_view(request):
    context = {
        "page_title": "My Profile",
        "recent_logins": LoginAttempt.objects.filter(
            user=request.user
        ).order_by("-created_at")[:10],
        "active_sessions": UserSession.objects.filter(
            user=request.user, is_active=True
        ).order_by("-last_seen"),
    }
    return render(request, "accounts/profile.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def security_view(request):
    context = {
        "page_title": "Security & Sessions",
        "login_history": LoginAttempt.objects.filter(
            user=request.user
        ).order_by("-created_at")[:50],
        "sessions": UserSession.objects.filter(user=request.user).order_by(
            "-last_seen"
        )[:50],
        "two_factor_enabled": request.user.two_factor_enabled,
    }
    return render(request, "accounts/security.html", context)


@login_required
@require_http_methods(["POST"])
def revoke_session_view(request, pk: int):
    session = get_object_or_404(UserSession, pk=pk, user=request.user)
    session.end()
    messages.success(request, "Session revoked.")
    return redirect("accounts:security")


@login_required
@require_http_methods(["GET", "POST"])
def two_factor_setup_view(request):
    """Enable or disable time-based one-time-password 2FA."""
    user = request.user
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "disable":
            user.two_factor_enabled = False
            user.totp_secret = ""
            user.save(update_fields=["two_factor_enabled", "totp_secret"])
            messages.info(request, "Two-factor authentication disabled.")
            return redirect("accounts:security")
        if action == "enable":
            secret = request.session.get("pending_totp_secret")
            code = request.POST.get("code", "")
            if secret and services.verify_totp(secret, code):
                user.totp_secret = secret
                user.two_factor_enabled = True
                user.save(update_fields=["two_factor_enabled", "totp_secret"])
                request.session.pop("pending_totp_secret", None)
                messages.success(
                    request, "Two-factor authentication enabled."
                )
                return redirect("accounts:security")
            messages.error(request, "Invalid code. Please try again.")

    secret = services.generate_totp_secret()
    request.session["pending_totp_secret"] = secret
    uri = services.get_totp_uri(user, secret)
    context = {
        "page_title": "Two-Factor Authentication",
        "secret": secret,
        "qr_data_uri": services.totp_qr_data_uri(uri),
    }
    return render(request, "accounts/two_factor_setup.html", context)
