"""URL configuration for the notifications app."""
from __future__ import annotations

from django.urls import path

from apps.notifications import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("dropdown/", views.dropdown, name="dropdown"),
    path("<int:pk>/read/", views.mark_read, name="mark_read"),
    path("mark-all-read/", views.mark_all_read, name="mark_all_read"),
    path("preferences/", views.preferences, name="preferences"),
    path("announcements/", views.announcement_list, name="announcements"),
    path("announcements/new/", views.announcement_create, name="announcement_create"),
]
