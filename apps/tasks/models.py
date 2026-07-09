"""Models for tasks, subtasks, comments, checklists and labels."""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.constants import Priority
from apps.core.models import BaseModel, TimeStampedModel
from apps.core.validators import validate_document_size


class TaskStatus(models.TextChoices):
    BACKLOG = "backlog", "Backlog"
    TODO = "todo", "To Do"
    IN_PROGRESS = "in_progress", "In Progress"
    REVIEW = "review", "In Review"
    DONE = "done", "Done"
    CANCELLED = "cancelled", "Cancelled"


# The ordered set of columns shown on the kanban board.
KANBAN_COLUMNS = [
    TaskStatus.BACKLOG,
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.REVIEW,
    TaskStatus.DONE,
]


class Label(TimeStampedModel):
    name = models.CharField(max_length=60, unique=True)
    color = models.CharField(max_length=7, default="#6b7280")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Task(BaseModel):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    milestone = models.ForeignKey(
        "projects.Milestone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subtasks",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )

    assignees = models.ManyToManyField(
        "employees.Employee", blank=True, related_name="tasks"
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_tasks",
    )
    labels = models.ManyToManyField(Label, blank=True, related_name="tasks")

    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    estimated_hours = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    logged_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0, db_index=True)

    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence = models.CharField(
        max_length=12,
        blank=True,
        choices=[
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
    )

    # Dependencies (finish-to-start)
    depends_on = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="dependents"
    )

    class Meta:
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=["status", "order"]),
            models.Index(fields=["project", "status"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("tasks:detail", kwargs={"pk": self.pk})

    @property
    def is_overdue(self) -> bool:
        return bool(
            self.due_date
            and self.due_date < timezone.localdate()
            and self.status not in {TaskStatus.DONE, TaskStatus.CANCELLED}
        )

    @property
    def is_done(self) -> bool:
        return self.status == TaskStatus.DONE

    @property
    def logged_hours(self) -> float:
        return round(self.logged_seconds / 3600, 2)

    @property
    def checklist_progress(self) -> int:
        items = self.checklist_items.all()
        total = len(items)
        if not total:
            return 0
        done = sum(1 for i in items if i.is_done)
        return int(round(done / total * 100))

    @property
    def subtask_count(self) -> int:
        return self.subtasks.count()

    def mark_done(self) -> None:
        self.status = TaskStatus.DONE
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])
        if self.project_id:
            self.project.recompute_progress()


class TaskComment(TimeStampedModel):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_comments",
    )
    body = models.TextField()
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="task_mentions"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.task}"


def task_attachment_path(instance, filename: str) -> str:
    return f"tasks/{instance.task_id}/{filename}"


class TaskAttachment(TimeStampedModel):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(
        upload_to=task_attachment_path, validators=[validate_document_size]
    )
    filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_attachments",
    )

    def __str__(self) -> str:
        return self.filename or str(self.file)

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name.rsplit("/", 1)[-1]
        super().save(*args, **kwargs)


class ChecklistItem(TimeStampedModel):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="checklist_items"
    )
    text = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return self.text


class TaskActivity(TimeStampedModel):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="activities"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_activities",
    )
    verb = models.CharField(max_length=120)
    detail = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Task activities"

    def __str__(self) -> str:
        return f"{self.actor} {self.verb}"
