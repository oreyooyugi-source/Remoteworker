"""URL configuration for the timetracking app."""
from __future__ import annotations

from django.urls import path

from apps.timetracking import views

app_name = "timetracking"

urlpatterns = [
    path("", views.timetracking_dashboard, name="dashboard"),
    path("timer/", views.timer_control, name="timer_control"),
    path("entries/", views.entry_list, name="entries"),
    path("entries/new/", views.manual_entry, name="manual_entry"),
    path("entries/<int:pk>/delete/", views.delete_entry, name="delete_entry"),
    # Timesheets
    path("timesheets/", views.timesheet_list, name="timesheet_list"),
    path("timesheets/<int:pk>/", views.timesheet_detail, name="timesheet_detail"),
    path("timesheets/<int:pk>/submit/", views.timesheet_submit, name="timesheet_submit"),
    path("timesheets/<int:pk>/decision/", views.timesheet_decision, name="timesheet_decision"),
]
