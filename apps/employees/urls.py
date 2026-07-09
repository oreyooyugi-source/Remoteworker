"""URL configuration for the employees app."""
from __future__ import annotations

from django.urls import path

from apps.employees import views

app_name = "employees"

urlpatterns = [
    path("", views.employee_list, name="list"),
    path("new/", views.employee_create, name="create"),
    path("org-chart/", views.org_chart, name="org_chart"),
    path("<int:pk>/", views.employee_detail, name="detail"),
    path("<int:pk>/edit/", views.employee_edit, name="edit"),
    path("<int:pk>/documents/", views.employee_documents, name="documents"),
    # Departments
    path("departments/", views.department_list, name="department_list"),
    path("departments/new/", views.department_create, name="department_create"),
    path("departments/<int:pk>/", views.department_detail, name="department_detail"),
    path("departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    # Teams
    path("teams/", views.team_list, name="team_list"),
    path("teams/new/", views.team_create, name="team_create"),
]
