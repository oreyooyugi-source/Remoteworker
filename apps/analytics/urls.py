"""URL configuration for the analytics app."""
from __future__ import annotations

from django.urls import path

from apps.analytics import views

app_name = "analytics"

urlpatterns = [
    path("", views.analytics_dashboard, name="dashboard"),
    path("workforce/", views.workforce_analytics, name="workforce"),
]
