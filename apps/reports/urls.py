"""URL configuration for the reports app."""
from __future__ import annotations

from django.urls import path

from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("builder/", views.report_builder, name="builder"),
    path("generate/", views.generate_report, name="generate"),
]
