"""Views for the employees app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.decorators import module_required
from apps.core.permissions import can_manage_employee, can_view_employee, is_hr
from apps.core.utils import paginate
from apps.employees import services
from apps.employees.forms import (
    DepartmentForm,
    DeviceForm,
    EmployeeDocumentForm,
    EmployeeFilterForm,
    EmployeeForm,
    TeamForm,
)
from apps.employees.models import (
    Branch,
    Department,
    Employee,
    JobTitle,
    Team,
)


@login_required
@module_required("employees")
def employee_list(request):
    form = EmployeeFilterForm(request.GET or None)
    employees = Employee.objects.all()

    if form.is_valid():
        if q := form.cleaned_data.get("q"):
            employees = employees.search(q)
        if dept := form.cleaned_data.get("department"):
            employees = employees.filter(department=dept)
        if status := form.cleaned_data.get("status"):
            employees = employees.filter(status=status)

    page = paginate(employees, request.GET.get("page"), per_page=24)
    context = {
        "page_title": "Employees",
        "page_subtitle": f"{employees.count()} people",
        "filter_form": form,
        "employees": page,
        "page_obj": page,
        "total": employees.count(),
    }
    return render(request, "employees/list.html", context)


@login_required
@module_required("employees")
def employee_detail(request, pk: int):
    employee = get_object_or_404(
        Employee.objects.select_related(
            "user", "department", "team", "job_title", "branch", "reports_to"
        ),
        pk=pk,
    )
    if not can_view_employee(request.user, employee):
        messages.error(request, "You are not allowed to view this employee.")
        return redirect("employees:list")

    context = {
        "page_title": employee.full_name,
        "page_subtitle": employee.job_title.name if employee.job_title else "",
        "employee": employee,
        "can_manage": can_manage_employee(request.user, employee),
        "documents": employee.documents.all()[:10],
        "devices": employee.devices.all(),
        "certifications": employee.certifications.all(),
        "emergency_contacts": employee.emergency_contacts.all(),
        "direct_reports": employee.direct_reports.select_related("user"),
    }
    return render(request, "employees/detail.html", context)


@login_required
@module_required("employees")
def employee_create(request):
    if not is_hr(request.user):
        messages.error(request, "Only HR can add employees.")
        return redirect("employees:list")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        form = EmployeeForm(request.POST)
        if email and form.is_valid() and first_name:
            employee = services.create_employee_with_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
            )
            for field, value in form.cleaned_data.items():
                if field == "skills":
                    continue
                setattr(employee, field, value)
            employee.save()
            if form.cleaned_data.get("skills"):
                employee.skills.set(form.cleaned_data["skills"])
            messages.success(request, f"Employee {employee.full_name} created.")
            return redirect(employee.get_absolute_url())
        messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()

    return render(
        request,
        "employees/form.html",
        {"page_title": "Add Employee", "form": form, "is_create": True},
    )


@login_required
@module_required("employees")
def employee_edit(request, pk: int):
    employee = get_object_or_404(Employee, pk=pk)
    if not can_manage_employee(request.user, employee):
        messages.error(request, "You cannot edit this employee.")
        return redirect(employee.get_absolute_url())

    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Employee updated.")
        return redirect(employee.get_absolute_url())
    return render(
        request,
        "employees/form.html",
        {"page_title": f"Edit {employee.full_name}", "form": form, "employee": employee},
    )


@login_required
@module_required("employees")
def employee_documents(request, pk: int):
    employee = get_object_or_404(Employee, pk=pk)
    if not can_view_employee(request.user, employee):
        return redirect("employees:list")

    if request.method == "POST" and can_manage_employee(request.user, employee):
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.save()
            messages.success(request, "Document uploaded.")
            return redirect("employees:documents", pk=pk)
    else:
        form = EmployeeDocumentForm()

    context = {
        "page_title": f"Documents — {employee.full_name}",
        "employee": employee,
        "documents": employee.documents.all(),
        "form": form,
        "can_manage": can_manage_employee(request.user, employee),
    }
    return render(request, "employees/documents.html", context)


@login_required
@module_required("employees")
def org_chart(request):
    context = {
        "page_title": "Organisation Chart",
        "tree": services.org_chart(),
    }
    return render(request, "employees/org_chart.html", context)


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------
@login_required
@module_required("employees")
def department_list(request):
    departments = Department.objects.annotate(
        headcount=Count("employees")
    ).select_related("manager__user", "branch")
    context = {
        "page_title": "Departments",
        "departments": departments,
        "headcount_data": services.department_headcount(),
    }
    return render(request, "employees/department_list.html", context)


@login_required
@module_required("employees")
def department_detail(request, pk: int):
    department = get_object_or_404(Department, pk=pk)
    employees = department.employees.select_related("user", "job_title")
    context = {
        "page_title": department.name,
        "department": department,
        "employees": employees,
        "teams": department.teams.all(),
    }
    return render(request, "employees/department_detail.html", context)


@login_required
@module_required("employees")
def department_create(request):
    if not is_hr(request.user):
        return redirect("employees:department_list")
    form = DepartmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department created.")
        return redirect("employees:department_list")
    return render(
        request,
        "employees/department_form.html",
        {"page_title": "New Department", "form": form},
    )


@login_required
@module_required("employees")
def department_edit(request, pk: int):
    department = get_object_or_404(Department, pk=pk)
    if not is_hr(request.user):
        return redirect("employees:department_list")
    form = DepartmentForm(request.POST or None, instance=department)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Department updated.")
        return redirect("employees:department_detail", pk=pk)
    return render(
        request,
        "employees/department_form.html",
        {"page_title": f"Edit {department.name}", "form": form},
    )


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------
@login_required
@module_required("employees")
def team_list(request):
    teams = Team.objects.select_related("department", "lead__user").annotate(
        members_total=Count("members")
    )
    context = {"page_title": "Teams", "teams": teams}
    return render(request, "employees/team_list.html", context)


@login_required
@module_required("employees")
def team_create(request):
    if not is_hr(request.user):
        return redirect("employees:team_list")
    form = TeamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Team created.")
        return redirect("employees:team_list")
    return render(
        request,
        "employees/team_form.html",
        {"page_title": "New Team", "form": form},
    )
