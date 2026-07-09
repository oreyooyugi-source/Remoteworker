"""Views for the reports app."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.audit import services as audit
from apps.audit.models import AuditAction
from apps.core.decorators import module_required
from apps.core.utils import paginate
from apps.reports import services
from apps.reports.models import Report, ReportFormat, ReportType


@login_required
@module_required("reports")
def report_list(request):
    reports = Report.objects.select_related("generated_by")
    page = paginate(reports, request.GET.get("page"), per_page=20)
    context = {
        "page_title": "Reports",
        "page_subtitle": "Generate and export data",
        "reports": page,
        "page_obj": page,
        "report_types": ReportType.choices,
        "formats": ReportFormat.choices,
    }
    return render(request, "reports/list.html", context)


@login_required
@module_required("reports")
def generate_report(request):
    if request.method != "POST":
        return redirect("reports:list")

    report_type = request.POST.get("report_type", ReportType.EMPLOYEE)
    export_format = request.POST.get("export_format", ReportFormat.CSV)
    params = {
        "start": request.POST.get("start", ""),
        "end": request.POST.get("end", ""),
    }

    if report_type not in ReportType.values:
        messages.error(request, "Unknown report type.")
        return redirect("reports:list")

    # Record the report generation for auditing / history.
    headers, rows, title = services.build_dataset(report_type, params)
    Report.objects.create(
        name=title,
        report_type=report_type,
        export_format=export_format,
        parameters=params,
        generated_by=request.user,
        row_count=len(rows),
        status=Report.Status.READY,
    )
    audit.log(
        AuditAction.EXPORT,
        module="reports",
        description=f"Generated {title} ({export_format}).",
        request=request,
    )
    return services.export(report_type, export_format, params)


@login_required
@module_required("reports")
def report_builder(request):
    context = {
        "page_title": "Report Builder",
        "report_types": ReportType.choices,
        "formats": ReportFormat.choices,
    }
    return render(request, "reports/builder.html", context)
