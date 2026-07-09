"""Core views: dashboards, health checks, error handlers and preferences."""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core import services


@login_required
def dashboard(request):
    """Render a role-appropriate dashboard."""
    data = services.build_dashboard(request.user)
    context = {
        "page_title": "Dashboard",
        "page_subtitle": f"{data.role_label} overview",
        "dashboard": data,
        "stat_cards": data.stat_cards,
        "charts_json": json.dumps(data.charts),
        "now": timezone.now(),
    }
    return render(request, "core/dashboard.html", context)


@login_required
def global_search(request):
    """Simple cross-module global search."""
    query = (request.GET.get("q") or "").strip()
    results: dict[str, list] = {
        "employees": [],
        "projects": [],
        "tasks": [],
    }
    if query and len(query) >= 2:
        try:
            from apps.employees.models import Employee

            results["employees"] = list(
                Employee.objects.search(query).select_related("user")[:10]
            )
        except Exception:  # noqa: BLE001
            pass
        try:
            from apps.projects.models import Project

            results["projects"] = list(
                Project.objects.filter(name__icontains=query)[:10]
            )
        except Exception:  # noqa: BLE001
            pass
        try:
            from apps.tasks.models import Task

            results["tasks"] = list(
                Task.objects.filter(title__icontains=query)[:10]
            )
        except Exception:  # noqa: BLE001
            pass

    context = {
        "page_title": "Search results",
        "query": query,
        "results": results,
        "total": sum(len(v) for v in results.values()),
    }
    return render(request, "core/search_results.html", context)


@require_POST
@login_required
def set_theme(request):
    """Persist the user's light/dark theme preference in the session."""
    theme = request.POST.get("theme", "light")
    if theme not in {"light", "dark"}:
        theme = "light"
    request.session["theme"] = theme
    # Persist to the user profile when possible.
    user = request.user
    if hasattr(user, "theme"):
        user.theme = theme
        user.save(update_fields=["theme"])
    return JsonResponse({"status": "ok", "theme": theme})


@require_POST
@login_required
def set_sidebar(request):
    """Persist the collapsed/expanded state of the sidebar."""
    collapsed = request.POST.get("collapsed") == "true"
    request.session["sidebar_collapsed"] = collapsed
    return JsonResponse({"status": "ok", "collapsed": collapsed})


def health_check(request):
    """Lightweight health-check endpoint for load balancers."""
    from django.db import connection

    db_ok = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # noqa: BLE001
        db_ok = False

    payload = {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "time": timezone.now().isoformat(),
    }
    return JsonResponse(payload, status=200 if db_ok else 503)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
def bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    return render(request, "errors/500.html", status=500)


def offline(request):
    """Served by the service worker when the network is unavailable."""
    return render(request, "errors/offline.html")
