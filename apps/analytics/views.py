"""Views for the analytics app."""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.analytics import services
from apps.core.decorators import module_required


@login_required
@module_required("analytics")
def analytics_dashboard(request):
    charts = {
        "headcount_by_department": services.headcount_by_department(),
        "productivity_distribution": services.productivity_distribution(),
        "attendance_trend": services.attendance_trend(30),
        "department_productivity": services.department_productivity(),
        "hours_trend": services.hours_trend(14),
        "forecast": services.forecast_productivity(7),
    }
    context = {
        "page_title": "Analytics",
        "page_subtitle": "Workforce insights & trends",
        "kpis": services.company_kpis(),
        "charts_json": json.dumps(charts),
        "heatmap_json": json.dumps(services.productivity_heatmap(28)),
    }
    return render(request, "analytics/dashboard.html", context)


@login_required
@module_required("analytics")
def workforce_analytics(request):
    context = {
        "page_title": "Workforce Analytics",
        "kpis": services.company_kpis(),
        "charts_json": json.dumps(
            {
                "headcount_by_department": services.headcount_by_department(),
                "attendance_trend": services.attendance_trend(30),
            }
        ),
    }
    return render(request, "analytics/workforce.html", context)
