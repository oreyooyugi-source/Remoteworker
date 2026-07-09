"""URL configuration for the monitoring app."""
from __future__ import annotations

from django.urls import path

from apps.monitoring import views

app_name = "monitoring"

urlpatterns = [
    path("", views.live_dashboard, name="live"),
    path("data/", views.live_data, name="live_data"),
    path("feed/", views.activity_feed, name="activity_feed"),
    path("employee/<int:pk>/", views.employee_monitor, name="employee"),
]
