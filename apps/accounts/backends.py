"""Custom authentication backends."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate against either the email address or the username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get("email")
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher to mitigate timing attacks.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = (
                User.objects.filter(
                    Q(username__iexact=username) | Q(email__iexact=username)
                )
                .order_by("id")
                .first()
            )
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
