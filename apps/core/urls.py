"""URL configuration for the core app."""
from __future__ import annotations

from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("search/", views.global_search, name="search"),
    path("preferences/theme/", views.set_theme, name="set_theme"),
    path("preferences/sidebar/", views.set_sidebar, name="set_sidebar"),
]
