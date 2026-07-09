"""Admin registrations for the employees app."""
from __future__ import annotations

from django.contrib import admin

from apps.core.admin import admin_site
from apps.employees.models import (
    BankInformation,
    Branch,
    Certification,
    Contract,
    Department,
    Device,
    Education,
    EmergencyContact,
    Employee,
    EmployeeDocument,
    EmploymentHistory,
    JobTitle,
    SalaryInformation,
    Skill,
    TaxInformation,
    Team,
)


class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 0


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0


class DocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0


@admin.register(Employee, site=admin_site)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_code",
        "full_name",
        "department",
        "job_title",
        "status",
        "online_status",
        "hire_date",
    )
    list_filter = ("status", "online_status", "employment_type", "department", "branch", "is_remote")
    search_fields = ("employee_code", "user__first_name", "user__last_name", "user__email")
    autocomplete_fields = ("user", "department", "team", "job_title", "branch", "reports_to")
    inlines = [EmergencyContactInline, DeviceInline, DocumentInline]
    date_hierarchy = "hire_date"
    list_select_related = ("user", "department", "job_title")


@admin.register(Department, site=admin_site)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "manager", "branch", "employee_count", "is_active")
    list_filter = ("is_active", "branch")
    search_fields = ("name", "code")


@admin.register(Team, site=admin_site)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "lead", "member_count", "is_active")
    list_filter = ("is_active", "department")
    search_fields = ("name",)


@admin.register(Branch, site=admin_site)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "city", "country", "is_active")
    list_filter = ("is_active", "country")
    search_fields = ("name", "code", "city")


@admin.register(JobTitle, site=admin_site)
class JobTitleAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "is_active")
    list_filter = ("is_active", "level")
    search_fields = ("name",)


@admin.register(Skill, site=admin_site)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name", "category")


for _model in (
    EmergencyContact,
    EmployeeDocument,
    Contract,
    EmploymentHistory,
    Education,
    Certification,
    Device,
    BankInformation,
    TaxInformation,
    SalaryInformation,
):
    admin_site.register(_model)
