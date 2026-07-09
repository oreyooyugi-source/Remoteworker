"""URL configuration for the tasks app."""
from __future__ import annotations

from django.urls import path

from apps.tasks import views

app_name = "tasks"

urlpatterns = [
    path("", views.task_list, name="list"),
    path("board/", views.task_board, name="board"),
    path("new/", views.task_create, name="create"),
    path("move/", views.task_move, name="move"),
    path("<int:pk>/", views.task_detail, name="detail"),
    path("<int:pk>/edit/", views.task_edit, name="edit"),
    path("<int:pk>/checklist/add/", views.checklist_add, name="checklist_add"),
    path("checklist/<int:pk>/toggle/", views.checklist_toggle, name="checklist_toggle"),
]
