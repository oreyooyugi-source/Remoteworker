"""URL configuration for the screenshots app."""
from __future__ import annotations

from django.urls import path

from apps.screenshots import views

app_name = "screenshots"

urlpatterns = [
    path("", views.screenshot_list, name="list"),
    path("timeline/", views.screenshot_timeline, name="timeline"),
    path("<int:pk>/", views.screenshot_detail, name="detail"),
    path("<int:pk>/flag/", views.screenshot_flag, name="flag"),
    path("<int:pk>/delete/", views.screenshot_delete, name="delete"),
]
