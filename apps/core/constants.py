"""Project-wide constants and enumerations used across applications."""
from __future__ import annotations

from django.db import models


class Role(models.TextChoices):
    """System roles that drive role-based access control."""

    SUPER_ADMIN = "super_admin", "Super Admin"
    COMPANY_ADMIN = "company_admin", "Company Admin"
    HR_MANAGER = "hr_manager", "HR Manager"
    DEPARTMENT_MANAGER = "department_manager", "Department Manager"
    PROJECT_MANAGER = "project_manager", "Project Manager"
    SUPERVISOR = "supervisor", "Supervisor"
    TEAM_LEAD = "team_lead", "Team Lead"
    EMPLOYEE = "employee", "Employee"
    AUDITOR = "auditor", "Auditor"
    READ_ONLY = "read_only", "Read-only User"


# Roles that can manage other people / see team-wide data.
MANAGEMENT_ROLES = {
    Role.SUPER_ADMIN,
    Role.COMPANY_ADMIN,
    Role.HR_MANAGER,
    Role.DEPARTMENT_MANAGER,
    Role.PROJECT_MANAGER,
    Role.SUPERVISOR,
    Role.TEAM_LEAD,
}

# Roles with elevated administrative privileges.
ADMIN_ROLES = {Role.SUPER_ADMIN, Role.COMPANY_ADMIN}


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    UNDISCLOSED = "undisclosed", "Prefer not to say"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full Time"
    PART_TIME = "part_time", "Part Time"
    CONTRACT = "contract", "Contract"
    INTERN = "intern", "Intern"
    FREELANCE = "freelance", "Freelance"
    TEMPORARY = "temporary", "Temporary"


class EmployeeStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ON_LEAVE = "on_leave", "On Leave"
    SUSPENDED = "suspended", "Suspended"
    TERMINATED = "terminated", "Terminated"
    PROBATION = "probation", "Probation"
    RESIGNED = "resigned", "Resigned"


class OnlineStatus(models.TextChoices):
    ONLINE = "online", "Online"
    IDLE = "idle", "Idle"
    WORKING = "working", "Working"
    BREAK = "break", "On Break"
    MEETING = "meeting", "In Meeting"
    OFFLINE = "offline", "Offline"


class Priority(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CANCELLED = "cancelled", "Cancelled"


# Colour map used by templates/badges for approval / generic statuses.
STATUS_COLORS = {
    "active": "success",
    "online": "success",
    "working": "success",
    "approved": "success",
    "completed": "success",
    "paid": "success",
    "idle": "warning",
    "break": "warning",
    "pending": "warning",
    "on_leave": "warning",
    "probation": "info",
    "meeting": "info",
    "in_progress": "info",
    "offline": "secondary",
    "resigned": "secondary",
    "cancelled": "secondary",
    "suspended": "danger",
    "terminated": "danger",
    "rejected": "danger",
    "critical": "danger",
    "high": "danger",
    "medium": "warning",
    "low": "info",
}
