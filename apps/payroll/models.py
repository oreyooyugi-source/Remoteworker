"""Models for payroll periods, payslips and pay components."""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class PayrollPeriod(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROCESSING = "processing", "Processing"
        APPROVED = "approved", "Approved"
        PAID = "paid", "Paid"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    pay_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-start_date"]
        unique_together = ("start_date", "end_date")

    def __str__(self) -> str:
        return self.name

    @property
    def total_net(self) -> Decimal:
        return sum((p.net_pay for p in self.payslips.all()), Decimal("0"))

    @property
    def payslip_count(self) -> int:
        return self.payslips.count()


class Payslip(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        PAID = "paid", "Paid"

    period = models.ForeignKey(
        PayrollPeriod, on_delete=models.CASCADE, related_name="payslips"
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="payslips",
    )
    reference = models.CharField(max_length=32, unique=True, blank=True)

    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    allowance_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deduction_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="USD")

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_payslips",
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("period", "employee")

    def __str__(self) -> str:
        return f"Payslip {self.reference} — {self.employee.full_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"PS-{timezone.now():%Y%m}-{Payslip.objects.count() + 1:05d}"
        super().save(*args, **kwargs)

    def recompute(self) -> None:
        earnings = self.components.filter(component_type=PayComponent.Type.EARNING)
        deductions = self.components.filter(component_type=PayComponent.Type.DEDUCTION)
        self.bonus_total = sum(
            (c.amount for c in earnings if c.category == "bonus"), Decimal("0")
        )
        self.allowance_total = sum(
            (c.amount for c in earnings if c.category == "allowance"), Decimal("0")
        )
        self.deduction_total = sum((c.amount for c in deductions), Decimal("0"))
        self.gross_pay = (
            self.base_salary
            + self.overtime_pay
            + self.bonus_total
            + self.allowance_total
        )
        self.net_pay = (
            self.gross_pay
            - self.tax_total
            - self.deduction_total
            - self.leave_deduction
        )

    def mark_paid(self) -> None:
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at"])


class PayComponent(TimeStampedModel):
    class Type(models.TextChoices):
        EARNING = "earning", "Earning"
        DEDUCTION = "deduction", "Deduction"

    payslip = models.ForeignKey(
        Payslip, on_delete=models.CASCADE, related_name="components"
    )
    component_type = models.CharField(max_length=10, choices=Type.choices)
    category = models.CharField(
        max_length=30,
        default="other",
        help_text="e.g. bonus, allowance, tax, insurance, loan",
    )
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_taxable = models.BooleanField(default=True)

    class Meta:
        ordering = ["component_type", "name"]

    def __str__(self) -> str:
        return f"{self.name}: {self.amount}"
