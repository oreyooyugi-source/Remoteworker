"""Views for the tasks app: kanban board, lists and details."""
from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import module_required
from apps.core.utils import paginate
from apps.tasks import services
from apps.tasks.forms import TaskCommentForm, TaskForm
from apps.tasks.models import Task, TaskStatus


@login_required
@module_required("tasks")
def task_board(request):
    project = None
    if pid := request.GET.get("project"):
        from apps.projects.models import Project

        project = Project.objects.filter(pk=pid).first()

    # Employees see only their own tasks unless filtering by project.
    assignee = None
    from apps.core.permissions import is_manager

    if not is_manager(request.user) and not project:
        assignee = getattr(request.user, "employee_profile", None)

    columns = services.board_data(project=project, assignee=assignee)
    context = {
        "page_title": "Task Board",
        "page_subtitle": project.name if project else "All tasks",
        "columns": columns,
        "project": project,
    }
    return render(request, "tasks/board.html", context)


@login_required
@module_required("tasks")
def task_list(request):
    tasks = Task.objects.select_related("project").prefetch_related("assignees__user")
    if status := request.GET.get("status"):
        tasks = tasks.filter(status=status)
    if priority := request.GET.get("priority"):
        tasks = tasks.filter(priority=priority)
    if q := request.GET.get("q"):
        tasks = tasks.filter(title__icontains=q)

    from apps.core.permissions import is_manager

    if not is_manager(request.user):
        employee = getattr(request.user, "employee_profile", None)
        if employee:
            tasks = tasks.filter(assignees=employee)

    page = paginate(tasks, request.GET.get("page"), per_page=25)
    context = {
        "page_title": "Tasks",
        "tasks": page,
        "page_obj": page,
        "statuses": TaskStatus.choices,
    }
    return render(request, "tasks/list.html", context)


@login_required
@module_required("tasks")
def task_detail(request, pk: int):
    task = get_object_or_404(
        Task.objects.select_related("project", "milestone", "reporter"), pk=pk
    )
    comment_form = TaskCommentForm(request.POST or None)
    if request.method == "POST" and comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        services.log_activity(task, request.user, "commented")
        messages.success(request, "Comment added.")
        return redirect(task.get_absolute_url())

    context = {
        "page_title": task.title,
        "task": task,
        "subtasks": task.subtasks.all(),
        "comments": task.comments.select_related("author"),
        "checklist": task.checklist_items.all(),
        "attachments": task.attachments.all(),
        "activities": task.activities.select_related("actor")[:20],
        "comment_form": comment_form,
    }
    return render(request, "tasks/detail.html", context)


@login_required
@module_required("tasks")
def task_create(request):
    initial = {}
    if pid := request.GET.get("project"):
        initial["project"] = pid
    if status := request.GET.get("status"):
        initial["status"] = status
    form = TaskForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.reporter = request.user
        task.save()
        form.save_m2m()
        if task.assignees.exists():
            services.assign_task(task, list(task.assignees.all()), actor=request.user)
        messages.success(request, "Task created.")
        return redirect(task.get_absolute_url())
    return render(
        request,
        "tasks/form.html",
        {"page_title": "New Task", "form": form},
    )


@login_required
@module_required("tasks")
def task_edit(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Task updated.")
        return redirect(task.get_absolute_url())
    return render(
        request,
        "tasks/form.html",
        {"page_title": f"Edit {task.title}", "form": form, "task": task},
    )


@login_required
@require_POST
def task_move(request):
    """AJAX endpoint used by the kanban drag-and-drop UI."""
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid payload."}, status=400)

    task_id = payload.get("task_id")
    new_status = payload.get("status")
    order = payload.get("order")

    if new_status not in TaskStatus.values:
        return JsonResponse({"error": "Invalid status."}, status=400)

    task = get_object_or_404(Task, pk=task_id)
    services.move_task(task, new_status, order=order, actor=request.user)
    return JsonResponse({"status": "ok", "task_id": task.id, "new_status": new_status})


@login_required
@require_POST
def checklist_toggle(request, pk: int):
    from apps.tasks.models import ChecklistItem

    item = get_object_or_404(ChecklistItem, pk=pk)
    item.is_done = not item.is_done
    item.save(update_fields=["is_done"])
    return JsonResponse(
        {"status": "ok", "is_done": item.is_done, "progress": item.task.checklist_progress}
    )


@login_required
@require_POST
def checklist_add(request, pk: int):
    from apps.tasks.models import ChecklistItem

    task = get_object_or_404(Task, pk=pk)
    text = request.POST.get("text", "").strip()
    if text:
        ChecklistItem.objects.create(task=task, text=text)
    return redirect(task.get_absolute_url())
