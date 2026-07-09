"""URL configuration for the accounts app."""
from __future__ import annotations

from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("2fa/", views.two_factor_view, name="two_factor"),
    # Password reset
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path(
        "reset/<str:token>/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
    path("change-password/", views.password_change_view, name="password_change"),
    # Email verification
    path("verify/<str:token>/", views.verify_email_view, name="verify_email"),
    # Profile & self-service
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("security/", views.security_view, name="security"),
    path(
        "security/sessions/<int:pk>/revoke/",
        views.revoke_session_view,
        name="revoke_session",
    ),
    path("security/2fa/setup/", views.two_factor_setup_view, name="two_factor_setup"),
]
