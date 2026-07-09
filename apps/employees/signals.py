"""Signal handlers for the employees app."""
from __future__ import annotations

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.employees.models import Employee


@receiver(pre_save, sender=Employee)
def assign_employee_code(sender, instance: Employee, **kwargs) -> None:
    """Generate a sequential employee code when one is not supplied."""
    if instance.employee_code:
        return
    year = timezone.now().year
    prefix = f"EMP-{year}-"
    last = (
        Employee.objects.filter(employee_code__startswith=prefix)
        .order_by("-employee_code")
        .first()
    )
    if last and last.employee_code[len(prefix):].isdigit():
        next_number = int(last.employee_code[len(prefix):]) + 1
    else:
        next_number = 1
    instance.employee_code = f"{prefix}{next_number:04d}"
