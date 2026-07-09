"""Admin registrations for the payroll app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.payroll.models import PayComponent, Payslip, PayrollPeriod


class PayComponentInline(admin.TabularInline):
    model = PayComponent
    extra = 0


@admin.register(PayrollPeriod, site=admin_site)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "status", "payslip_count", "total_net")
    list_filter = ("status",)
    date_hierarchy = "start_date"


@admin.register(Payslip, site=admin_site)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ("reference", "employee", "period", "gross_pay", "net_pay", "status")
    list_filter = ("status", "period")
    search_fields = ("reference", "employee__user__first_name", "employee__user__last_name")
    autocomplete_fields = ("employee",)
    inlines = [PayComponentInline]
