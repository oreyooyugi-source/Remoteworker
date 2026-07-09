"""URL configuration for the payroll app."""
from __future__ import annotations

from django.urls import path

from apps.payroll import views

app_name = "payroll"

urlpatterns = [
    path("", views.payroll_dashboard, name="dashboard"),
    path("periods/", views.period_list, name="period_list"),
    path("periods/new/", views.period_create, name="period_create"),
    path("periods/<int:pk>/", views.period_detail, name="period_detail"),
    path("periods/<int:pk>/run/", views.run_payroll, name="run_payroll"),
    path("periods/<int:pk>/pay/", views.mark_paid, name="mark_paid"),
    path("payslips/<int:pk>/", views.payslip_detail, name="payslip_detail"),
]
