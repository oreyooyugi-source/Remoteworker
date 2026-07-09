"""Views for the projects app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.decorators import module_required
from apps.core.permissions import is_manager
from apps.core.utils import paginate
from apps.projects.forms import ClientForm, MilestoneForm, ProjectForm
from apps.projects.models import Client, Project, ProjectStatus


@login_required
@module_required("projects")
def project_list(request):
    projects = Project.objects.select_related("client", "manager__user").annotate(
        num_tasks=Count("tasks")
    ).order_by("-created_at")
    if q := request.GET.get("q"):
        projects = projects.filter(Q(name__icontains=q) | Q(code__icontains=q))
    if status := request.GET.get("status"):
        projects = projects.filter(status=status)

    # Employees only see projects they're a member of.
    if not is_manager(request.user):
        employee = getattr(request.user, "employee_profile", None)
        if employee:
            projects = projects.filter(
                Q(members=employee) | Q(manager=employee)
            ).distinct()

    page = paginate(projects, request.GET.get("page"), per_page=12)
    context = {
        "page_title": "Projects",
        "projects": page,
        "page_obj": page,
        "statuses": ProjectStatus.choices,
        "active_count": Project.objects.filter(status=ProjectStatus.ACTIVE).count(),
        "can_manage": is_manager(request.user),
    }
    return render(request, "projects/list.html", context)


@login_required
@module_required("projects")
def project_detail(request, pk: int):
    project = get_object_or_404(
        Project.objects.select_related("client", "manager__user", "department"),
        pk=pk,
    )
    from apps.tasks.models import Task, TaskStatus

    tasks = Task.objects.filter(project=project)
    context = {
        "page_title": project.name,
        "page_subtitle": project.code,
        "project": project,
        "milestones": project.milestones.all(),
        "risks": project.risks.filter(is_resolved=False),
        "members": project.members.select_related("user"),
        "tasks_total": tasks.count(),
        "tasks_done": tasks.filter(status=TaskStatus.DONE).count(),
        "recent_tasks": tasks.order_by("-created_at")[:8],
        "can_manage": is_manager(request.user),
    }
    return render(request, "projects/detail.html", context)


@login_required
@module_required("projects")
def project_create(request):
    if not is_manager(request.user):
        messages.error(request, "You cannot create projects.")
        return redirect("projects:list")
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save()
        messages.success(request, f"Project '{project.name}' created.")
        return redirect(project.get_absolute_url())
    return render(
        request,
        "projects/form.html",
        {"page_title": "New Project", "form": form},
    )


@login_required
@module_required("projects")
def project_edit(request, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not is_manager(request.user):
        return redirect(project.get_absolute_url())
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project updated.")
        return redirect(project.get_absolute_url())
    return render(
        request,
        "projects/form.html",
        {"page_title": f"Edit {project.name}", "form": form, "project": project},
    )


@login_required
@module_required("projects")
def project_board(request, pk: int):
    """Kanban board scoped to a single project (delegates to tasks board)."""
    return redirect(f"/tasks/board/?project={pk}")


@login_required
@module_required("projects")
def milestone_create(request, pk: int):
    project = get_object_or_404(Project, pk=pk)
    if not is_manager(request.user):
        return redirect(project.get_absolute_url())
    form = MilestoneForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        milestone = form.save(commit=False)
        milestone.project = project
        milestone.save()
        messages.success(request, "Milestone added.")
        return redirect(project.get_absolute_url())
    return render(
        request,
        "projects/milestone_form.html",
        {"page_title": "New Milestone", "form": form, "project": project},
    )


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
@login_required
@module_required("projects")
def client_list(request):
    clients = Client.objects.annotate(num_projects=Count("projects"))
    context = {"page_title": "Clients", "clients": clients}
    return render(request, "projects/client_list.html", context)


@login_required
@module_required("projects")
def client_create(request):
    if not is_manager(request.user):
        return redirect("projects:client_list")
    form = ClientForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Client created.")
        return redirect("projects:client_list")
    return render(
        request,
        "projects/client_form.html",
        {"page_title": "New Client", "form": form},
    )
