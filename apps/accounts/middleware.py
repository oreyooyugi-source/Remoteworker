"""Session-management middleware for the accounts app."""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


class SessionTimeoutMiddleware:
    """Log users out after a configurable period of inactivity."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "SESSION_COOKIE_AGE", 3600)

    def __call__(self, request):
        if request.user.is_authenticated:
            last_touch = request.session.get("_last_touch")
            now_ts = timezone.now().timestamp()
            if last_touch and (now_ts - last_touch) > self.timeout:
                logout(request)
                messages.info(
                    request,
                    "Your session expired due to inactivity. Please sign in "
                    "again.",
                )
                return redirect(reverse("accounts:login"))
            request.session["_last_touch"] = now_ts
        return self.get_response(request)


class LastActivityMiddleware:
    """Record the timestamp of a user's most recent request (throttled)."""

    THROTTLE_SECONDS = 60

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            last = user.last_activity
            now = timezone.now()
            if not last or (now - last).total_seconds() > self.THROTTLE_SECONDS:
                from django.contrib.auth import get_user_model

                # Update without triggering a full save signal storm.
                get_user_model().objects.filter(pk=user.pk).update(
                    last_activity=now
                )
        return response
