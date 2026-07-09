"""URL configuration for the attendance app."""
from __future__ import annotations

from django.urls import path

from apps.attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_dashboard, name="dashboard"),
    path("clock/", views.clock_action, name="clock_action"),
    path("records/", views.attendance_records, name="records"),
    path("team/", views.team_attendance, name="team"),
    path("correction/", views.correction_request, name="correction"),
    # Leave
    path("leave/", views.leave_list, name="leave_list"),
    path("leave/request/", views.leave_request, name="leave_request"),
    path("leave/<int:pk>/decision/", views.leave_decision, name="leave_decision"),
]
