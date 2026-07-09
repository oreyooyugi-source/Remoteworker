"""Management command that seeds the database with realistic demo data.

Usage examples::

    python manage.py seed_data                 # default (40 employees, 30 days)
    python manage.py seed_data --employees 120 --days 60
    python manage.py seed_data --flush          # wipe demo data first
"""
from __future__ import annotations

import datetime
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.core.constants import (
    EmployeeStatus,
    EmploymentType,
    Gender,
    OnlineStatus,
    Priority,
    Role,
)

User = get_user_model()

FIRST_NAMES = [
    "Olivia", "Liam", "Emma", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "Lucas", "Mia", "Oliver", "Amelia", "Elijah", "Harper",
    "James", "Evelyn", "Benjamin", "Abigail", "Henry", "Emily", "Alexander",
    "Ella", "Sebastian", "Grace", "Jack", "Chloe", "Aiden", "Victoria",
    "Daniel", "Aria", "Matthew", "Scarlett", "Samuel", "Zoey", "David",
    "Lily", "Joseph", "Nora", "Carter", "Layla", "Owen", "Riley", "Wyatt",
    "Priya", "Arjun", "Mei", "Kenji", "Amara", "Diego", "Fatima", "Yusuf",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Clark", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott",
    "Nguyen", "Patel", "Kim", "Chen", "Okafor", "Silva", "Haddad", "Rossi",
]

DEPARTMENTS = [
    ("Engineering", "ENG", "#2563eb"),
    ("Product", "PRD", "#7c3aed"),
    ("Design", "DSN", "#db2777"),
    ("Marketing", "MKT", "#f59e0b"),
    ("Sales", "SAL", "#16a34a"),
    ("Customer Success", "CS", "#0891b2"),
    ("Human Resources", "HR", "#dc2626"),
    ("Finance", "FIN", "#4f46e5"),
    ("Operations", "OPS", "#0d9488"),
    ("IT Support", "IT", "#64748b"),
]

JOB_TITLES = [
    ("Software Engineer", 3), ("Senior Software Engineer", 4),
    ("Engineering Manager", 6), ("Product Manager", 5),
    ("UX Designer", 3), ("UI Designer", 3), ("Marketing Specialist", 2),
    ("Sales Representative", 2), ("Account Executive", 4),
    ("Customer Success Manager", 4), ("HR Business Partner", 4),
    ("Financial Analyst", 3), ("Operations Coordinator", 2),
    ("IT Support Specialist", 2), ("Data Analyst", 3), ("QA Engineer", 3),
    ("DevOps Engineer", 4), ("Team Lead", 5), ("Director", 7), ("Intern", 1),
]

SKILLS = [
    ("Python", "Technical"), ("JavaScript", "Technical"), ("React", "Technical"),
    ("Django", "Technical"), ("SQL", "Technical"), ("AWS", "Technical"),
    ("Docker", "Technical"), ("Figma", "Design"), ("UI/UX", "Design"),
    ("Project Management", "Soft"), ("Communication", "Soft"),
    ("Leadership", "Soft"), ("SEO", "Marketing"), ("Copywriting", "Marketing"),
    ("Sales", "Business"), ("Negotiation", "Business"), ("Accounting", "Finance"),
    ("Data Analysis", "Technical"), ("Machine Learning", "Technical"),
    ("Customer Support", "Soft"),
]

PRODUCTIVE_APPS = ["VS Code", "PyCharm", "IntelliJ IDEA", "Figma", "Slack",
                   "Microsoft Teams", "Jira", "Confluence", "Excel", "Terminal",
                   "Postman", "Notion", "Google Docs"]
NEUTRAL_APPS = ["Chrome", "Firefox", "Outlook", "Zoom", "File Explorer",
                "Spotify", "Calculator"]
UNPRODUCTIVE_APPS = ["YouTube", "Instagram", "Facebook", "TikTok", "Netflix",
                     "Reddit", "Twitter"]

PRODUCTIVE_SITES = ["github.com", "stackoverflow.com", "docs.python.org",
                    "atlassian.net", "figma.com", "notion.so", "aws.amazon.com"]
NEUTRAL_SITES = ["google.com", "wikipedia.org", "mail.google.com", "linkedin.com"]
UNPRODUCTIVE_SITES = ["youtube.com", "facebook.com", "instagram.com",
                      "reddit.com", "twitter.com", "netflix.com"]

CLIENT_NAMES = ["Globex Corporation", "Initech", "Umbrella Industries",
                "Stark Enterprises", "Wayne Enterprises", "Acme Retail",
                "Hooli", "Pied Piper", "Soylent Corp", "Vandelay Industries",
                "Cyberdyne Systems", "Wonka Industries"]

PROJECT_NAMES = ["Website Redesign", "Mobile App v2", "Data Platform Migration",
                 "Customer Portal", "Payment Gateway", "Analytics Dashboard",
                 "Marketing Campaign Q3", "Internal Tools Revamp",
                 "API Gateway", "Cloud Infrastructure", "CRM Integration",
                 "E-commerce Checkout", "Security Audit", "Onboarding Flow",
                 "Reporting Engine"]

TASK_VERBS = ["Implement", "Design", "Fix", "Refactor", "Review", "Test",
              "Document", "Deploy", "Optimize", "Investigate", "Update",
              "Create", "Integrate", "Configure"]
TASK_NOUNS = ["login flow", "dashboard widget", "API endpoint", "database schema",
              "user profile page", "notification system", "search feature",
              "payment integration", "report export", "onboarding wizard",
              "settings panel", "email template", "caching layer", "CI pipeline"]

LABELS = [("Bug", "#dc2626"), ("Feature", "#2563eb"), ("Enhancement", "#16a34a"),
          ("Documentation", "#7c3aed"), ("Urgent", "#f59e0b"),
          ("Backend", "#0891b2"), ("Frontend", "#db2777"), ("Research", "#64748b")]


class Command(BaseCommand):
    help = "Seed the database with realistic demonstration data."

    def add_arguments(self, parser):
        parser.add_argument("--employees", type=int, default=40,
                            help="Number of employees to create.")
        parser.add_argument("--days", type=int, default=30,
                            help="Days of historical activity to generate.")
        parser.add_argument("--flush", action="store_true",
                            help="Delete existing demo data before seeding.")
        parser.add_argument("--password", type=str, default="Passw0rd!2026",
                            help="Password assigned to every seeded user.")

    def handle(self, *args, **options):
        self.employees_count = options["employees"]
        self.days = options["days"]
        self.password = options["password"]
        random.seed(42)

        if options["flush"]:
            self._flush()

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo data..."))
        with transaction.atomic():
            self._seed_company()
            self._seed_reference_data()
            self._seed_departments_teams()
            self._seed_employees()
            self._seed_projects_tasks()
        # Activity data can be large; keep outside the big atomic block.
        self._seed_attendance()
        self._seed_time_tracking()
        self._seed_monitoring_and_productivity()
        self._seed_screenshots()
        self._seed_payroll()
        self._seed_notifications()
        self._seed_audit()

        self.stdout.write(self.style.SUCCESS("\n== Seeding complete! =="))
        self.stdout.write(
            f"  Admin login:  admin@rwt.local\n"
            f"  Demo users:   <name>@rwt.local  /  password: {self.password}\n"
            f"  Employees:    {self.employees_count} · History: {self.days} days"
        )

    # ------------------------------------------------------------------ flush
    def _flush(self):
        self.stdout.write(self.style.WARNING("Flushing existing demo data..."))
        from apps.attendance.models import AttendanceRecord, LeaveRequest
        from apps.audit.models import AuditLog
        from apps.employees.models import Branch, Department, Employee
        from apps.monitoring.models import ActivitySession, ApplicationUsage, WebsiteUsage
        from apps.notifications.models import Announcement, Notification
        from apps.payroll.models import PayrollPeriod
        from apps.productivity.models import ProductivityRecord
        from apps.projects.models import Client, Project
        from apps.screenshots.models import Screenshot
        from apps.tasks.models import Label, Task
        from apps.timetracking.models import TimeEntry, Timesheet

        for model in [Screenshot, ApplicationUsage, WebsiteUsage, ActivitySession,
                      ProductivityRecord, AttendanceRecord, LeaveRequest, TimeEntry,
                      Timesheet, Task, Label, Project, Client, PayrollPeriod,
                      Notification, Announcement, AuditLog]:
            model.objects.all().delete()
        Employee.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        Department.objects.all().delete()
        Branch.objects.all().delete()

    # ---------------------------------------------------------------- company
    def _seed_company(self):
        from apps.settings_app.models import CompanySettings

        company = CompanySettings.load()
        company.company_name = "Nimbus Technologies Inc."
        company.legal_name = "Nimbus Technologies Incorporated"
        company.tagline = "Building the future of remote work"
        company.email = "hello@nimbus.example"
        company.website = "https://nimbus.example"
        company.currency = "USD"
        company.currency_symbol = "$"
        company.save()
        self._log("Company settings")

    # -------------------------------------------------------------- reference
    def _seed_reference_data(self):
        from apps.attendance.models import Shift
        from apps.employees.models import Branch, JobTitle, Skill
        from apps.settings_app.models import (
            HolidayCalendar, Holiday, LeaveType, ProductivityRule,
            WorkingHoursPolicy,
        )

        self.branches = []
        for name, city, country in [
            ("HQ — San Francisco", "San Francisco", "USA"),
            ("London Office", "London", "UK"),
            ("Bangalore Hub", "Bangalore", "India"),
            ("Remote", "", ""),
        ]:
            self.branches.append(Branch.objects.create(
                name=name, code=name[:8].upper().replace(" ", ""),
                city=city, country=country,
            ))

        self.job_titles = [
            JobTitle.objects.create(name=n, level=lvl) for n, lvl in JOB_TITLES
        ]
        self.skills = [
            Skill.objects.create(name=n, category=c) for n, c in SKILLS
        ]

        Shift.objects.create(name="Day Shift", start_time="09:00", end_time="17:00")
        Shift.objects.create(name="Night Shift", start_time="22:00",
                             end_time="06:00", is_night_shift=True)

        WorkingHoursPolicy.objects.create(name="Standard 9-5", is_default=True)
        WorkingHoursPolicy.objects.create(name="Flexible Hours", flexible=True)

        for name, code, days, paid in [
            ("Annual Leave", "AL", 25, True), ("Sick Leave", "SL", 10, True),
            ("Personal Leave", "PL", 5, True), ("Unpaid Leave", "UL", 0, False),
            ("Parental Leave", "PAL", 90, True),
        ]:
            LeaveType.objects.create(name=name, code=code, days_per_year=days, is_paid=paid)

        cal = HolidayCalendar.objects.create(name="Company Holidays",
                                             year=timezone.now().year)
        for name, month, day in [("New Year's Day", 1, 1), ("Independence Day", 7, 4),
                                 ("Thanksgiving", 11, 27), ("Christmas Day", 12, 25)]:
            Holiday.objects.create(calendar=cal, name=name,
                                   date=datetime.date(timezone.now().year, month, day))

        for app in PRODUCTIVE_APPS + PRODUCTIVE_SITES:
            ProductivityRule.objects.create(name=app, pattern=app, category="productive")
        for app in UNPRODUCTIVE_APPS + UNPRODUCTIVE_SITES:
            ProductivityRule.objects.create(name=app, pattern=app, category="unproductive")
        self._log("Reference data (branches, titles, skills, shifts, policies)")

    # ------------------------------------------------------- departments/teams
    def _seed_departments_teams(self):
        from apps.employees.models import Department, Team

        self.departments = []
        for name, code, color in DEPARTMENTS:
            self.departments.append(Department.objects.create(
                name=name, code=code, color=color,
                branch=random.choice(self.branches),
                description=f"The {name} department.",
            ))

        self.teams = []
        for dept in self.departments:
            for suffix in ["Alpha", "Beta"]:
                self.teams.append(Team.objects.create(
                    name=f"{dept.code} {suffix}", department=dept,
                ))
        self._log(f"{len(self.departments)} departments, {len(self.teams)} teams")

    # ------------------------------------------------------------- employees
    def _seed_employees(self):
        from apps.employees.models import (
            BankInformation, Employee, SalaryInformation, TaxInformation,
        )

        self.employees = []
        used_emails = set()
        role_pool = (
            [Role.HR_MANAGER] * 2 + [Role.DEPARTMENT_MANAGER] * 4
            + [Role.PROJECT_MANAGER] * 3 + [Role.TEAM_LEAD] * 4
            + [Role.SUPERVISOR] * 2 + [Role.AUDITOR] * 1
        )

        for i in range(self.employees_count):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            base_email = f"{first.lower()}.{last.lower()}"
            email = f"{base_email}@rwt.local"
            n = 1
            while email in used_emails:
                n += 1
                email = f"{base_email}{n}@rwt.local"
            used_emails.add(email)

            role = role_pool[i] if i < len(role_pool) else Role.EMPLOYEE
            user = User.objects.create_user(
                email=email, username=email.split("@")[0], password=self.password,
                first_name=first, last_name=last, role=role,
                email_verified=True,
                is_staff=role in {Role.HR_MANAGER, Role.DEPARTMENT_MANAGER},
            )
            dept = random.choice(self.departments)
            team = random.choice([t for t in self.teams if t.department_id == dept.id])
            employee = Employee.objects.create(
                user=user, department=dept, team=team,
                job_title=random.choice(self.job_titles),
                branch=random.choice(self.branches),
                employment_type=random.choice(list(EmploymentType.values)),
                status=EmployeeStatus.ACTIVE,
                gender=random.choice(list(Gender.values)),
                hire_date=timezone.localdate() - datetime.timedelta(
                    days=random.randint(30, 2000)),
                online_status=random.choice([
                    OnlineStatus.WORKING, OnlineStatus.IDLE, OnlineStatus.OFFLINE,
                    OnlineStatus.OFFLINE, OnlineStatus.BREAK, OnlineStatus.MEETING,
                ]),
                last_seen=timezone.now() - datetime.timedelta(minutes=random.randint(0, 300)),
                hourly_rate=Decimal(random.randint(25, 90)),
                phone=f"+1 555 {random.randint(1000000, 9999999)}",
                city=random.choice(["San Francisco", "London", "Bangalore", "Austin", "Berlin"]),
                country=random.choice(["USA", "UK", "India", "Germany"]),
            )
            employee.skills.set(random.sample(self.skills, k=random.randint(2, 6)))
            SalaryInformation.objects.create(
                employee=employee,
                base_salary=Decimal(random.randint(4000, 12000)),
            )
            TaxInformation.objects.create(employee=employee, tax_id=f"TAX{random.randint(10000, 99999)}")
            BankInformation.objects.create(
                employee=employee, bank_name="Demo Bank",
                account_holder=employee.full_name,
                account_number=str(random.randint(10**11, 10**12)),
            )
            self.employees.append(employee)

        # Assign managers / reporting lines.
        managers = [e for e in self.employees if e.user.role in {
            Role.DEPARTMENT_MANAGER, Role.TEAM_LEAD, Role.PROJECT_MANAGER}]
        for employee in self.employees:
            if employee not in managers and managers:
                candidate = random.choice(managers)
                if candidate.id != employee.id:
                    employee.reports_to = candidate
                    employee.save(update_fields=["reports_to"])
        # Assign department managers.
        for dept in self.departments:
            dept_managers = [e for e in managers if e.department_id == dept.id]
            if dept_managers:
                dept.manager = dept_managers[0]
                dept.save(update_fields=["manager"])
        self._log(f"{len(self.employees)} employees with salary/tax/bank records")

    # --------------------------------------------------------- projects/tasks
    def _seed_projects_tasks(self):
        from apps.projects.models import Client, Milestone, Project, ProjectRisk
        from apps.tasks.models import ChecklistItem, Label, Task, TaskComment, TaskStatus

        clients = [Client.objects.create(
            name=name, contact_name=random.choice(FIRST_NAMES),
            email=f"contact@{name.split()[0].lower()}.example",
        ) for name in CLIENT_NAMES]

        labels = [Label.objects.create(name=n, color=c) for n, c in LABELS]

        managers = [e for e in self.employees if e.user.role in {
            Role.PROJECT_MANAGER, Role.DEPARTMENT_MANAGER}] or self.employees

        self.projects = []
        for name in PROJECT_NAMES:
            project = Project.objects.create(
                name=name, description=f"Delivery of the {name} initiative.",
                client=random.choice(clients),
                manager=random.choice(managers),
                department=random.choice(self.departments),
                status=random.choice(["planning", "active", "active", "active", "on_hold", "completed"]),
                priority=random.choice(list(Priority.values)),
                start_date=timezone.localdate() - datetime.timedelta(days=random.randint(10, 300)),
                due_date=timezone.localdate() + datetime.timedelta(days=random.randint(10, 180)),
                budget=Decimal(random.randint(20000, 200000)),
                spent=Decimal(random.randint(5000, 150000)),
            )
            project.members.set(random.sample(self.employees, k=random.randint(3, 8)))
            for m in range(random.randint(2, 4)):
                Milestone.objects.create(
                    project=project, name=f"Phase {m + 1}",
                    due_date=timezone.localdate() + datetime.timedelta(days=30 * (m + 1)),
                    order=m, is_completed=random.random() < 0.3,
                )
            for _ in range(random.randint(0, 2)):
                ProjectRisk.objects.create(
                    project=project, title=random.choice([
                        "Scope creep", "Resource shortage", "Third-party delay",
                        "Budget overrun", "Technical debt"]),
                    likelihood=random.choice(list(Priority.values)),
                    impact=random.choice(list(Priority.values)),
                )
            self.projects.append(project)

        # Tasks per project.
        statuses = list(TaskStatus.values)
        self.tasks = []
        for project in self.projects:
            members = list(project.members.all()) or self.employees
            for _ in range(random.randint(8, 18)):
                title = f"{random.choice(TASK_VERBS)} {random.choice(TASK_NOUNS)}"
                status = random.choice(statuses)
                task = Task.objects.create(
                    project=project, title=title,
                    description="Auto-generated demo task.",
                    status=status, priority=random.choice(list(Priority.values)),
                    reporter=random.choice(members).user,
                    due_date=timezone.localdate() + datetime.timedelta(days=random.randint(-10, 40)),
                    estimated_hours=Decimal(random.randint(1, 24)),
                    order=random.randint(0, 100),
                    completed_at=timezone.now() if status == TaskStatus.DONE else None,
                )
                task.assignees.set(random.sample(members, k=min(len(members), random.randint(1, 3))))
                task.labels.set(random.sample(labels, k=random.randint(0, 3)))
                for c in range(random.randint(0, 4)):
                    ChecklistItem.objects.create(
                        task=task, text=f"Subtask step {c + 1}",
                        is_done=random.random() < 0.5, order=c)
                for _ in range(random.randint(0, 3)):
                    TaskComment.objects.create(
                        task=task, author=random.choice(members).user,
                        body=random.choice([
                            "Looks good to me!", "Can you add more detail?",
                            "Blocked on the API team.", "Merged and deployed.",
                            "Great work on this."]))
                self.tasks.append(task)
            project.recompute_progress()
        self._log(f"{len(clients)} clients, {len(self.projects)} projects, {len(self.tasks)} tasks")

    # ------------------------------------------------------------- attendance
    def _seed_attendance(self):
        from apps.attendance.models import AttendanceRecord, AttendanceStatus

        records = []
        today = timezone.localdate()
        for employee in self.employees:
            for offset in range(self.days):
                day = today - datetime.timedelta(days=offset)
                if day.weekday() >= 5:  # weekend
                    continue
                roll = random.random()
                if roll < 0.05:
                    records.append(AttendanceRecord(
                        employee=employee, date=day, status=AttendanceStatus.ABSENT))
                    continue
                if roll < 0.10:
                    records.append(AttendanceRecord(
                        employee=employee, date=day, status=AttendanceStatus.ON_LEAVE))
                    continue
                start_hour = 9
                late = random.random() < 0.15
                minute = random.randint(0, 20) + (random.randint(20, 55) if late else 0)
                clock_in = timezone.make_aware(datetime.datetime.combine(
                    day, datetime.time(start_hour, min(minute, 59))))
                worked = random.randint(6, 9) * 3600 + random.randint(0, 3599)
                clock_out = clock_in + datetime.timedelta(seconds=worked + 3600)
                records.append(AttendanceRecord(
                    employee=employee, date=day,
                    status=AttendanceStatus.LATE if late else random.choice(
                        [AttendanceStatus.PRESENT, AttendanceStatus.REMOTE]),
                    clock_in=clock_in, clock_out=clock_out,
                    worked_seconds=worked, break_seconds=3600,
                    overtime_seconds=max(worked - 8 * 3600, 0),
                    is_late=late, late_minutes=minute if late else 0,
                ))
        AttendanceRecord.objects.bulk_create(records, batch_size=500)
        self._log(f"{len(records)} attendance records")

    # ---------------------------------------------------------- time tracking
    def _seed_time_tracking(self):
        from apps.timetracking.models import TimeEntry

        entries = []
        today = timezone.localdate()
        for employee in self.employees:
            emp_projects = [p for p in self.projects
                            if employee in p.members.all()] or self.projects
            for offset in range(min(self.days, 20)):
                day = today - datetime.timedelta(days=offset)
                if day.weekday() >= 5:
                    continue
                for _ in range(random.randint(1, 3)):
                    start = timezone.make_aware(datetime.datetime.combine(
                        day, datetime.time(random.randint(9, 15), random.randint(0, 59))))
                    duration = random.randint(1800, 10800)
                    entries.append(TimeEntry(
                        employee=employee, project=random.choice(emp_projects),
                        description=f"{random.choice(TASK_VERBS)} {random.choice(TASK_NOUNS)}",
                        start_time=start, end_time=start + datetime.timedelta(seconds=duration),
                        duration_seconds=duration, is_billable=random.random() < 0.7,
                        is_manual=True, hourly_rate=employee.hourly_rate,
                    ))
        TimeEntry.objects.bulk_create(entries, batch_size=500)
        self._log(f"{len(entries)} time entries")

    # -------------------------------------------------- monitoring/productivity
    def _seed_monitoring_and_productivity(self):
        from apps.monitoring.models import (
            ActivitySession, ApplicationUsage, DeviceMetric, WebsiteUsage,
        )
        from apps.productivity.models import ProductivityRecord
        from apps.productivity.services import compute_score

        sessions, app_usage, web_usage, metrics, prod_records = [], [], [], [], []
        today = timezone.localdate()
        for employee in self.employees:
            for offset in range(self.days):
                day = today - datetime.timedelta(days=offset)
                if day.weekday() >= 5 or random.random() < 0.1:
                    continue
                active = random.randint(4, 8) * 3600 + random.randint(0, 3599)
                idle = random.randint(0, 3) * 3600 + random.randint(0, 3599)
                start = timezone.make_aware(datetime.datetime.combine(day, datetime.time(9, 0)))
                session = ActivitySession(
                    employee=employee, started_at=start,
                    ended_at=start + datetime.timedelta(seconds=active + idle),
                    active_seconds=active, idle_seconds=idle,
                    break_seconds=random.randint(1800, 3600),
                    meeting_seconds=random.randint(0, 7200),
                    keyboard_events=random.randint(2000, 20000),
                    mouse_events=random.randint(1000, 15000),
                    operating_system=random.choice(["Windows", "macOS", "Linux"]),
                    browser=random.choice(["Chrome", "Firefox", "Edge"]),
                    hostname=f"host-{employee.id}", is_active=False,
                    monitor_count=random.randint(1, 3),
                )
                sessions.append(session)

        ActivitySession.objects.bulk_create(sessions, batch_size=500)

        # Build usage + productivity from persisted sessions.
        for session in ActivitySession.objects.filter(
                employee__in=self.employees).iterator():
            day = timezone.localtime(session.started_at).date()
            prod_sec = 0
            unprod_sec = 0
            for app in random.sample(PRODUCTIVE_APPS, k=3):
                secs = random.randint(1800, 9000)
                prod_sec += secs
                app_usage.append(ApplicationUsage(
                    employee=session.employee, date=day, application=app,
                    category="productive", seconds=secs))
            for app in random.sample(UNPRODUCTIVE_APPS, k=2):
                secs = random.randint(300, 3600)
                unprod_sec += secs
                app_usage.append(ApplicationUsage(
                    employee=session.employee, date=day, application=app,
                    category="unproductive", seconds=secs))
            for site in random.sample(PRODUCTIVE_SITES, k=2):
                web_usage.append(WebsiteUsage(
                    employee=session.employee, date=day, domain=site,
                    category="productive", seconds=random.randint(600, 5400),
                    visits=random.randint(1, 20)))
            for site in random.sample(UNPRODUCTIVE_SITES, k=2):
                web_usage.append(WebsiteUsage(
                    employee=session.employee, date=day, domain=site,
                    category="unproductive", seconds=random.randint(300, 2400),
                    visits=random.randint(1, 15)))
            metrics.append(DeviceMetric(
                employee=session.employee, session=session,
                cpu_percent=random.uniform(5, 85), ram_percent=random.uniform(30, 90),
                disk_percent=random.uniform(40, 95),
                battery_percent=random.uniform(20, 100),
                network_status="online", download_mbps=random.uniform(20, 200),
                upload_mbps=random.uniform(5, 50), ping_ms=random.uniform(5, 80)))

            focus = max(session.active_seconds - session.meeting_seconds, 0)
            scores = compute_score(session.active_seconds, session.idle_seconds,
                                   prod_sec, unprod_sec, focus, True)
            prod_records.append(ProductivityRecord(
                employee=session.employee, date=day, **scores,
                active_seconds=session.active_seconds, idle_seconds=session.idle_seconds,
                focus_seconds=focus, break_seconds=session.break_seconds,
                meeting_seconds=session.meeting_seconds,
                productive_seconds=prod_sec, unproductive_seconds=unprod_sec,
                tasks_completed=random.randint(0, 5)))

        # Deduplicate usage by (employee, date, app/domain) to satisfy unique constraints.
        ApplicationUsage.objects.bulk_create(
            self._dedupe(app_usage, lambda o: (o.employee_id, o.date, o.application)),
            batch_size=500, ignore_conflicts=True)
        WebsiteUsage.objects.bulk_create(
            self._dedupe(web_usage, lambda o: (o.employee_id, o.date, o.domain)),
            batch_size=500, ignore_conflicts=True)
        DeviceMetric.objects.bulk_create(metrics, batch_size=500)
        ProductivityRecord.objects.bulk_create(
            self._dedupe(prod_records, lambda o: (o.employee_id, o.date)),
            batch_size=500, ignore_conflicts=True)
        self._log(f"{len(sessions)} sessions, {len(prod_records)} productivity records")

    # ------------------------------------------------------------- screenshots
    def _seed_screenshots(self):
        from apps.screenshots.models import Screenshot

        shots = []
        today = timezone.localdate()
        for employee in random.sample(self.employees, k=min(len(self.employees), 15)):
            for offset in range(min(self.days, 7)):
                day = today - datetime.timedelta(days=offset)
                if day.weekday() >= 5:
                    continue
                for _ in range(random.randint(2, 6)):
                    captured = timezone.make_aware(datetime.datetime.combine(
                        day, datetime.time(random.randint(9, 17), random.randint(0, 59))))
                    shots.append(Screenshot(
                        employee=employee, captured_at=captured,
                        active_application=random.choice(PRODUCTIVE_APPS),
                        activity_level=random.randint(20, 100),
                        is_flagged=random.random() < 0.05,
                        width=1920, height=1080))
        Screenshot.objects.bulk_create(shots, batch_size=500)
        self._log(f"{len(shots)} screenshot records (metadata)")

    # ----------------------------------------------------------------- payroll
    def _seed_payroll(self):
        from apps.payroll.models import PayrollPeriod
        from apps.payroll.services import run_payroll

        first_of_month = timezone.localdate().replace(day=1)
        last_month_end = first_of_month - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        period = PayrollPeriod.objects.create(
            name=last_month_start.strftime("Payroll — %B %Y"),
            start_date=last_month_start, end_date=last_month_end,
        )
        run_payroll(period)
        self._log(f"Payroll period '{period.name}' with {period.payslip_count} payslips")

    # ----------------------------------------------------------- notifications
    def _seed_notifications(self):
        from apps.notifications.models import Announcement, NotificationType
        from apps.notifications.services import notify

        for employee in random.sample(self.employees, k=min(len(self.employees), 25)):
            for _ in range(random.randint(1, 4)):
                notify(
                    employee.user,
                    title=random.choice([
                        "New task assigned", "Timesheet approved",
                        "Leave request update", "Weekly report ready",
                        "Meeting reminder"]),
                    message="This is a demo notification.",
                    notification_type=random.choice(list(NotificationType.values)),
                    send_email=False,
                )
        admin = User.objects.filter(is_superuser=True).first()
        for title, body in [
            ("Welcome to Nimbus!", "We're excited to launch our new workforce platform."),
            ("Q3 All-Hands", "Join us for the quarterly all-hands next Friday."),
            ("New Leave Policy", "Please review the updated leave policy in Settings."),
        ]:
            Announcement.objects.create(title=title, body=body, author=admin, pinned=title.startswith("Welcome"))
        self._log("Notifications and announcements")

    # ----------------------------------------------------------------- audit
    def _seed_audit(self):
        from apps.audit.models import AuditAction, AuditLog

        actions = list(AuditAction.values)
        logs = []
        for employee in random.sample(self.employees, k=min(len(self.employees), 30)):
            for _ in range(random.randint(1, 5)):
                logs.append(AuditLog(
                    actor=employee.user, actor_repr=str(employee.user),
                    action=random.choice(actions),
                    module=random.choice(["employees", "attendance", "tasks",
                                          "projects", "payroll", "accounts"]),
                    description="Demo audit event.",
                    ip_address=f"10.0.{random.randint(0,255)}.{random.randint(1,254)}",
                ))
        AuditLog.objects.bulk_create(logs, batch_size=500)
        self._log(f"{len(logs)} audit log entries")

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _dedupe(objects, key):
        seen = set()
        result = []
        for obj in objects:
            k = key(obj)
            if k not in seen:
                seen.add(k)
                result.append(obj)
        return result

    def _log(self, message):
        self.stdout.write(self.style.SUCCESS(f"  [+] {message}"))
