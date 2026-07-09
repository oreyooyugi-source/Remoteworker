"""Models for clients, projects, milestones and risks."""
from __future__ import annotations

from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.constants import Priority
from apps.core.models import BaseModel, TimeStampedModel
from apps.core.utils import unique_slug


class ProjectStatus(models.TextChoices):
    PLANNING = "planning", "Planning"
    ACTIVE = "active", "Active"
    ON_HOLD = "on_hold", "On Hold"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Client(TimeStampedModel):
    name = models.CharField(max_length=160)
    contact_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to="clients/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def project_count(self) -> int:
        return self.projects.count()


class Project(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True)

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    manager = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_projects",
    )
    members = models.ManyToManyField(
        "employees.Employee", blank=True, related_name="projects"
    )
    department = models.ForeignKey(
        "employees.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )

    status = models.CharField(
        max_length=12,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PLANNING,
        db_index=True,
    )
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    color = models.CharField(max_length=7, default="#2563eb")

    start_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)

    budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    is_billable = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    progress = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "priority"])]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Project, self.name)
        if not self.code:
            self.code = f"PRJ-{timezone.now():%y}{Project.objects.count() + 1:04d}"
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("projects:detail", kwargs={"pk": self.pk})

    @property
    def is_overdue(self) -> bool:
        return bool(
            self.due_date
            and self.due_date < timezone.localdate()
            and self.status not in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}
        )

    @property
    def budget_used_percent(self) -> float:
        if not self.budget:
            return 0.0
        return round(min(float(self.spent) / float(self.budget) * 100, 100), 1)

    @property
    def health(self) -> str:
        """Simple RAG health indicator."""
        if self.status == ProjectStatus.CANCELLED:
            return "danger"
        if self.is_overdue or self.budget_used_percent > 90:
            return "danger"
        if self.budget_used_percent > 75 or (self.progress < 40 and self.status == ProjectStatus.ACTIVE):
            return "warning"
        return "success"

    def recompute_progress(self) -> None:
        """Set progress from the completion ratio of child tasks."""
        from apps.tasks.models import Task, TaskStatus

        tasks = Task.objects.filter(project=self)
        total = tasks.count()
        if not total:
            return
        done = tasks.filter(status=TaskStatus.DONE).count()
        self.progress = int(round(done / total * 100))
        if self.progress == 100 and self.status == ProjectStatus.ACTIVE:
            self.status = ProjectStatus.COMPLETED
            self.completed_date = timezone.localdate()
        self.save(update_fields=["progress", "status", "completed_date"])

    @property
    def task_count(self) -> int:
        return self.tasks.count()


class Milestone(TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="milestones"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "due_date"]

    def __str__(self) -> str:
        return f"{self.name} ({self.project.name})"

    def mark_complete(self) -> None:
        self.is_completed = True
        self.completed_date = timezone.localdate()
        self.save(update_fields=["is_completed", "completed_date"])


class ProjectRisk(TimeStampedModel):
    class Likelihood(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="risks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    likelihood = models.CharField(
        max_length=10, choices=Likelihood.choices, default=Likelihood.MEDIUM
    )
    impact = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    mitigation = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title
