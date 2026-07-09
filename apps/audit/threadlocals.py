"""Thread-local storage for the currently-processing request.

This lets signal handlers (which do not receive the request) attribute
changes to the acting user and capture request metadata.
"""
from __future__ import annotations

import threading

_state = threading.local()


def set_current_request(request) -> None:
    _state.request = request


def get_current_request():
    return getattr(_state, "request", None)


def get_current_user():
    request = get_current_request()
    if request is None:
        return None
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user
    return None


def clear() -> None:
    if hasattr(_state, "request"):
        del _state.request
