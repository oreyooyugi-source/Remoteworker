"""URL configuration for the productivity app."""
from __future__ import annotations

from django.urls import path

from apps.productivity import views

app_name = "productivity"

urlpatterns = [
    path("", views.productivity_dashboard, name="dashboard"),
    path("records/", views.productivity_records, name="records"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("employee/<int:pk>/", views.employee_productivity, name="employee"),
]
