"""URL configuration for the audit app."""
from __future__ import annotations

from django.urls import path

from apps.audit import views

app_name = "audit"

urlpatterns = [
    path("", views.audit_list, name="list"),
    path("<int:pk>/", views.audit_detail, name="detail"),
]
