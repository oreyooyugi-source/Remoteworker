"""Tests for the tasks app."""
from __future__ import annotations

from django.test import TestCase

from apps.projects.models import Project
from apps.tasks import services
from apps.tasks.models import Task, TaskStatus


class TaskTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")

    def test_move_task_updates_status(self):
        task = Task.objects.create(title="Do it", project=self.project)
        services.move_task(task, TaskStatus.IN_PROGRESS)
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

    def test_mark_done_updates_project_progress(self):
        task = Task.objects.create(title="Finish", project=self.project)
        task.mark_done()
        self.project.refresh_from_db()
        self.assertEqual(self.project.progress, 100)

    def test_board_data_columns(self):
        Task.objects.create(title="A", project=self.project, status=TaskStatus.TODO)
        Task.objects.create(title="B", project=self.project, status=TaskStatus.DONE)
        columns = services.board_data(project=self.project)
        self.assertEqual(len(columns), 5)
        todo = next(c for c in columns if c["status"] == TaskStatus.TODO)
        self.assertEqual(todo["count"], 1)

    def test_overdue(self):
        import datetime

        task = Task.objects.create(
            title="Late", project=self.project, due_date=datetime.date(2000, 1, 1)
        )
        self.assertTrue(task.is_overdue)
