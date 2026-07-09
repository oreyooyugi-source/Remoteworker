"""Signals for the attendance app."""
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.attendance.models import LeaveRequest
from apps.audit import services as audit
from apps.core.constants import ApprovalStatus
from apps.notifications import services as notify
from apps.notifications.models import NotificationType


@receiver(post_save, sender=LeaveRequest)
def notify_leave_decision(sender, instance: LeaveRequest, created, **kwargs):
    """Notify the employee when their leave request is decided."""
    if created:
        # Notify approvers (managers / HR) about a new request.
        audit.log(
            "create",
            target=instance,
            module="attendance",
            description=f"Leave request submitted by {instance.employee.full_name}.",
        )
        return

    if instance.status in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
        verb = "approved" if instance.status == ApprovalStatus.APPROVED else "rejected"
        notify.notify(
            instance.employee.user,
            title=f"Leave request {verb}",
            message=(
                f"Your leave from {instance.start_date} to {instance.end_date} "
                f"was {verb}."
            ),
            notification_type=NotificationType.LEAVE,
            icon="fa-plane-departure",
            url="/attendance/leave/",
        )
