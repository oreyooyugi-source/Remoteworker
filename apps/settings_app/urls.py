"""URL configuration for the settings app."""
from __future__ import annotations

from django.urls import path

from apps.settings_app import views

app_name = "settings_app"

urlpatterns = [
    path("", views.settings_index, name="index"),
    path("company/", views.company_settings_view, name="company"),
    path("working-hours/", views.working_hours_list, name="working_hours"),
    path("working-hours/new/", views.working_hours_edit, name="working_hours_create"),
    path("working-hours/<int:pk>/", views.working_hours_edit, name="working_hours_edit"),
    path("leave-types/", views.leave_types, name="leave_types"),
    path("productivity-rules/", views.productivity_rules, name="productivity_rules"),
    path("holidays/", views.holiday_calendars, name="holidays"),
]
