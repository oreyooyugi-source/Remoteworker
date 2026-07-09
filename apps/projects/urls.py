"""URL configuration for the projects app."""
from __future__ import annotations

from django.urls import path

from apps.projects import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("new/", views.project_create, name="create"),
    path("clients/", views.client_list, name="client_list"),
    path("clients/new/", views.client_create, name="client_create"),
    path("<int:pk>/", views.project_detail, name="detail"),
    path("<int:pk>/edit/", views.project_edit, name="edit"),
    path("<int:pk>/board/", views.project_board, name="board"),
    path("<int:pk>/milestones/new/", views.milestone_create, name="milestone_create"),
]
