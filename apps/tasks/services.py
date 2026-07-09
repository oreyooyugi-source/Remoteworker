"""Business logic for the tasks app."""
from __future__ import annotations

from django.utils import timezone

from apps.notifications import services as notify
from apps.notifications.models import NotificationType
from apps.tasks.models import Task, TaskActivity, TaskStatus


def log_activity(task: Task, actor, verb: str, detail: str = "") -> TaskActivity:
    return TaskActivity.objects.create(
        task=task, actor=actor, verb=verb, detail=detail
    )


def move_task(task: Task, new_status: str, order: int | None = None, actor=None) -> Task:
    """Move a task to a new kanban column (status) and reorder."""
    old_status = task.status
    task.status = new_status
    if order is not None:
        task.order = order
    if new_status == TaskStatus.DONE and old_status != TaskStatus.DONE:
        task.completed_at = timezone.now()
    task.save(update_fields=["status", "order", "completed_at"])

    if old_status != new_status:
        log_activity(
            task,
            actor,
            "moved task",
            f"{old_status} → {new_status}",
        )
        if task.project_id:
            task.project.recompute_progress()
    return task


def assign_task(task: Task, employees, actor=None) -> None:
    """Assign employees to a task and notify them."""
    task.assignees.set(employees)
    for employee in employees:
        if employee.user_id == getattr(actor, "id", None):
            continue
        notify.notify(
            employee.user,
            title="New task assigned",
            message=task.title,
            notification_type=NotificationType.TASK,
            icon="fa-list-check",
            url=task.get_absolute_url(),
            actor=actor,
        )
    log_activity(task, actor, "updated assignees")


def board_data(project=None, assignee=None):
    """Return tasks grouped by kanban column."""
    from apps.tasks.models import KANBAN_COLUMNS

    tasks = Task.objects.filter(parent__isnull=True).prefetch_related(
        "assignees__user", "labels"
    )
    if project is not None:
        tasks = tasks.filter(project=project)
    if assignee is not None:
        tasks = tasks.filter(assignees=assignee)

    columns = []
    for status in KANBAN_COLUMNS:
        column_tasks = [t for t in tasks if t.status == status]
        column_tasks.sort(key=lambda t: t.order)
        columns.append(
            {
                "status": status,
                "label": status.label,
                "tasks": column_tasks,
                "count": len(column_tasks),
            }
        )
    return columns
