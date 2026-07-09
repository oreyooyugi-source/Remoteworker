"""Models for employee records, org structure and HR data."""
from __future__ import annotations

import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.constants import (
    EmployeeStatus,
    EmploymentType,
    Gender,
    OnlineStatus,
)
from apps.core.models import BaseModel, TimeStampedModel
from apps.core.validators import phone_validator, validate_document_size
from apps.employees.managers import EmployeeManager


class Branch(TimeStampedModel):
    """A physical office / branch location."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    timezone = models.CharField(max_length=64, default="UTC")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Branches"

    def __str__(self) -> str:
        return self.name


class Department(TimeStampedModel):
    """An organisational department."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sub_departments",
    )
    manager = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="departments",
    )
    color = models.CharField(max_length=7, default="#2563eb")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("employees:department_detail", kwargs={"pk": self.pk})

    @property
    def employee_count(self) -> int:
        return self.employees.count()


class Team(TimeStampedModel):
    """A team within a department."""

    name = models.CharField(max_length=120)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="teams"
    )
    lead = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "department")

    def __str__(self) -> str:
        return f"{self.name} ({self.department.name})"

    @property
    def member_count(self) -> int:
        return self.members.count()


class JobTitle(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    level = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["level", "name"]

    def __str__(self) -> str:
        return self.name


class Skill(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Employee(BaseModel):
    """The central employee profile, linked one-to-one with a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_profile",
    )
    employee_code = models.CharField(max_length=32, unique=True, db_index=True)

    # Organisation
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    job_title = models.ForeignKey(
        JobTitle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    reports_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="direct_reports",
    )
    skills = models.ManyToManyField(Skill, blank=True, related_name="employees")

    # Personal
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=16, choices=Gender.choices, blank=True
    )
    marital_status = models.CharField(max_length=20, blank=True)
    nationality = models.CharField(max_length=60, blank=True)
    personal_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=80, blank=True)

    # Employment
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    status = models.CharField(
        max_length=20,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE,
        db_index=True,
    )
    hire_date = models.DateField(default=timezone.localdate)
    probation_end_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    is_remote = models.BooleanField(default=True)

    # Presence / monitoring
    online_status = models.CharField(
        max_length=16,
        choices=OnlineStatus.choices,
        default=OnlineStatus.OFFLINE,
        db_index=True,
    )
    last_seen = models.DateTimeField(null=True, blank=True)
    current_activity = models.CharField(max_length=255, blank=True)

    # Compensation snapshot (detailed records live on SalaryInformation)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    weekly_hours = models.PositiveSmallIntegerField(default=40)

    objects = EmployeeManager()

    class Meta:
        ordering = ["employee_code"]
        indexes = [
            models.Index(fields=["status", "online_status"]),
            models.Index(fields=["department", "team"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.employee_code})"

    def get_absolute_url(self) -> str:
        return reverse("employees:detail", kwargs={"pk": self.pk})

    @property
    def full_name(self) -> str:
        return self.user.get_full_name()

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def avatar_url(self) -> str:
        return self.user.avatar_url

    @property
    def initials(self) -> str:
        return self.user.initials

    @property
    def is_online(self) -> bool:
        return self.online_status in {
            OnlineStatus.ONLINE,
            OnlineStatus.WORKING,
            OnlineStatus.MEETING,
        }

    @property
    def tenure_days(self) -> int:
        end = self.termination_date or timezone.localdate()
        return (end - self.hire_date).days

    @property
    def tenure_display(self) -> str:
        days = self.tenure_days
        years, remainder = divmod(days, 365)
        months = remainder // 30
        parts = []
        if years:
            parts.append(f"{years}y")
        if months:
            parts.append(f"{months}m")
        return " ".join(parts) or "New"

    @property
    def age(self) -> int | None:
        if not self.date_of_birth:
            return None
        today = timezone.localdate()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def set_online_status(self, status: str) -> None:
        self.online_status = status
        self.last_seen = timezone.now()
        self.save(update_fields=["online_status", "last_seen"])


class EmergencyContact(TimeStampedModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="emergency_contacts"
    )
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=60)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.relationship})"


def document_upload_path(instance, filename: str) -> str:
    return f"documents/employee_{instance.employee_id}/{filename}"


class EmployeeDocument(TimeStampedModel):
    class DocumentType(models.TextChoices):
        ID = "id", "ID / Passport"
        CONTRACT = "contract", "Contract"
        CERTIFICATE = "certificate", "Certificate"
        RESUME = "resume", "Resume / CV"
        OFFER = "offer", "Offer Letter"
        NDA = "nda", "NDA"
        OTHER = "other", "Other"

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="documents"
    )
    title = models.CharField(max_length=160)
    document_type = models.CharField(
        max_length=20, choices=DocumentType.choices, default=DocumentType.OTHER
    )
    file = models.FileField(
        upload_to=document_upload_path, validators=[validate_document_size]
    )
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_expired(self) -> bool:
        return bool(self.expiry_date and self.expiry_date < timezone.localdate())


class Contract(TimeStampedModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="contracts"
    )
    title = models.CharField(max_length=160)
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    file = models.FileField(
        upload_to="contracts/", blank=True, null=True, validators=[validate_document_size]
    )
    is_signed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.title} — {self.employee.full_name}"


class EmploymentHistory(TimeStampedModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="employment_history"
    )
    company = models.CharField(max_length=160)
    job_title = models.CharField(max_length=160)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name_plural = "Employment history"

    def __str__(self) -> str:
        return f"{self.job_title} @ {self.company}"


class Education(TimeStampedModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="education"
    )
    institution = models.CharField(max_length=160)
    degree = models.CharField(max_length=120)
    field_of_study = models.CharField(max_length=120, blank=True)
    start_year = models.PositiveIntegerField(null=True, blank=True)
    end_year = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=40, blank=True)

    class Meta:
        ordering = ["-end_year"]
        verbose_name_plural = "Education"

    def __str__(self) -> str:
        return f"{self.degree} — {self.institution}"


class Certification(TimeStampedModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="certifications"
    )
    name = models.CharField(max_length=160)
    issuing_organization = models.CharField(max_length=160)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self) -> str:
        return self.name


class Device(TimeStampedModel):
    class DeviceType(models.TextChoices):
        LAPTOP = "laptop", "Laptop"
        DESKTOP = "desktop", "Desktop"
        MOBILE = "mobile", "Mobile"
        TABLET = "tablet", "Tablet"
        OTHER = "other", "Other"

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="devices"
    )
    name = models.CharField(max_length=120)
    device_type = models.CharField(
        max_length=20, choices=DeviceType.choices, default=DeviceType.LAPTOP
    )
    serial_number = models.CharField(max_length=120, blank=True)
    operating_system = models.CharField(max_length=80, blank=True)
    mac_address = models.CharField(max_length=32, blank=True)
    assigned_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_device_type_display()})"


class BankInformation(TimeStampedModel):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="bank_information"
    )
    bank_name = models.CharField(max_length=120)
    account_holder = models.CharField(max_length=120)
    account_number = models.CharField(max_length=64)
    routing_number = models.CharField(max_length=64, blank=True)
    iban = models.CharField(max_length=64, blank=True)
    swift_code = models.CharField(max_length=32, blank=True)
    currency = models.CharField(max_length=3, default="USD")

    class Meta:
        verbose_name = "Bank information"
        verbose_name_plural = "Bank information"

    def __str__(self) -> str:
        return f"{self.bank_name} — {self.employee.full_name}"

    @property
    def masked_account(self) -> str:
        if len(self.account_number) <= 4:
            return "••••"
        return "•••• " + self.account_number[-4:]


class TaxInformation(TimeStampedModel):
    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="tax_information"
    )
    tax_id = models.CharField(max_length=64, blank=True)
    tax_class = models.CharField(max_length=64, blank=True)
    filing_status = models.CharField(max_length=64, blank=True)
    allowances = models.PositiveSmallIntegerField(default=0)
    additional_withholding = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "Tax information"
        verbose_name_plural = "Tax information"

    def __str__(self) -> str:
        return f"Tax — {self.employee.full_name}"


class SalaryInformation(TimeStampedModel):
    class PayFrequency(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Bi-weekly"
        MONTHLY = "monthly", "Monthly"
        ANNUAL = "annual", "Annual"

    employee = models.OneToOneField(
        Employee, on_delete=models.CASCADE, related_name="salary_information"
    )
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")
    pay_frequency = models.CharField(
        max_length=20,
        choices=PayFrequency.choices,
        default=PayFrequency.MONTHLY,
    )
    effective_date = models.DateField(default=timezone.localdate)
    overtime_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.5
    )

    class Meta:
        verbose_name = "Salary information"
        verbose_name_plural = "Salary information"

    def __str__(self) -> str:
        return f"Salary — {self.employee.full_name}"
