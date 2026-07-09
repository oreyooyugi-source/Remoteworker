"""Views for browsing the audit log."""
from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.audit.models import AuditAction, AuditLog
from apps.core.decorators import module_required
from apps.core.utils import paginate


@login_required
@module_required("audit")
def audit_list(request):
    logs = AuditLog.objects.select_related("actor")

    action = request.GET.get("action")
    module = request.GET.get("module")
    actor = request.GET.get("actor")
    q = request.GET.get("q")

    if action:
        logs = logs.filter(action=action)
    if module:
        logs = logs.filter(module=module)
    if actor:
        logs = logs.filter(actor_id=actor)
    if q:
        logs = logs.filter(description__icontains=q)

    page = paginate(logs, request.GET.get("page"), per_page=40)
    context = {
        "page_title": "Audit Log",
        "page_subtitle": "Immutable record of every action",
        "logs": page,
        "page_obj": page,
        "actions": AuditAction.choices,
        "modules": (
            AuditLog.objects.exclude(module="")
            .values_list("module", flat=True)
            .distinct()
            .order_by("module")
        ),
        "selected_action": action or "",
        "selected_module": module or "",
        "query": q or "",
    }
    return render(request, "audit/list.html", context)


@login_required
@module_required("audit")
def audit_detail(request, pk: int):
    log = get_object_or_404(AuditLog.objects.select_related("actor"), pk=pk)
    return render(
        request,
        "audit/detail.html",
        {"page_title": "Audit Entry", "log": log},
    )
