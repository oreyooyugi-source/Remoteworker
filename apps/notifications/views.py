"""Views for notifications, preferences and announcements."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.utils import paginate
from apps.notifications import services
from apps.notifications.forms import AnnouncementForm, NotificationPreferenceForm
from apps.notifications.models import Announcement, Notification


@login_required
def notification_list(request):
    qs = Notification.objects.filter(recipient=request.user).select_related("actor")
    unread_only = request.GET.get("filter") == "unread"
    if unread_only:
        qs = qs.filter(is_read=False)
    page = paginate(qs, request.GET.get("page"), per_page=25)
    context = {
        "page_title": "Notifications",
        "notifications": page,
        "page_obj": page,
        "unread_only": unread_only,
        "unread_total": services.unread_count(request.user),
    }
    return render(request, "notifications/list.html", context)


@login_required
@require_POST
def mark_read(request, pk: int):
    notification = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    notification.mark_read()
    if request.headers.get("HX-Request") or request.headers.get(
        "x-requested-with"
    ) == "XMLHttpRequest":
        return JsonResponse(
            {"status": "ok", "unread": services.unread_count(request.user)}
        )
    return redirect(notification.get_absolute_url())


@login_required
@require_POST
def mark_all_read(request):
    services.mark_all_read(request.user)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "ok", "unread": 0})
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications:list")


@login_required
def dropdown(request):
    """HTMX/AJAX partial that renders the notification dropdown contents."""
    recent = Notification.objects.filter(
        recipient=request.user
    ).select_related("actor")[:10]
    return render(
        request,
        "notifications/partials/dropdown.html",
        {
            "recent_notifications": recent,
            "unread_notifications": services.unread_count(request.user),
        },
    )


@login_required
def preferences(request):
    prefs = services.get_preferences(request.user)
    form = NotificationPreferenceForm(request.POST or None, instance=prefs)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Notification preferences saved.")
        return redirect("notifications:preferences")
    return render(
        request,
        "notifications/preferences.html",
        {"page_title": "Notification Preferences", "form": form},
    )


# ---------------------------------------------------------------------------
# Announcements
# ---------------------------------------------------------------------------
@login_required
def announcement_list(request):
    announcements = Announcement.objects.filter(is_published=True).select_related(
        "author", "department"
    )
    context = {
        "page_title": "Announcements",
        "announcements": announcements,
    }
    return render(request, "notifications/announcements.html", context)


@login_required
def announcement_create(request):
    from apps.core.permissions import is_manager

    if not is_manager(request.user):
        messages.error(request, "You cannot post announcements.")
        return redirect("notifications:announcements")

    form = AnnouncementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        announcement = form.save(commit=False)
        announcement.author = request.user
        announcement.save()
        _broadcast_announcement(announcement)
        messages.success(request, "Announcement published.")
        return redirect("notifications:announcements")
    return render(
        request,
        "notifications/announcement_form.html",
        {"page_title": "New Announcement", "form": form},
    )


def _broadcast_announcement(announcement: Announcement) -> None:
    from django.contrib.auth import get_user_model

    from apps.notifications.models import NotificationType

    User = get_user_model()
    recipients = User.objects.filter(is_active=True)
    if announcement.department_id:
        recipients = recipients.filter(
            employee_profile__department_id=announcement.department_id
        )
    services.notify_many(
        recipients,
        title=announcement.title,
        message=announcement.body[:200],
        notification_type=NotificationType.ANNOUNCEMENT,
        priority=announcement.priority,
        icon="fa-bullhorn",
        actor=announcement.author,
    )
