"""Audit middleware: capture the current request and log auth events."""
from __future__ import annotations

from apps.audit import threadlocals


class AuditLogMiddleware:
    """Store the active request in thread-local storage for signal access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        threadlocals.set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            threadlocals.clear()
        return response
