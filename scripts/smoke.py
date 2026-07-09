"""Ad-hoc smoke test: log in and GET every module page, reporting status codes.

Run with:  python manage.py shell -c "exec(open('scripts/smoke.py').read())"
"""
from django.test import Client

c = Client()
assert c.login(email="admin@rwt.local", password="Admin!Passw0rd2026"), "login failed"

paths = [
    "/", "/employees/", "/employees/departments/", "/employees/teams/",
    "/employees/org-chart/", "/employees/new/",
    "/attendance/", "/attendance/records/", "/attendance/team/",
    "/attendance/leave/", "/attendance/leave/request/",
    "/time/", "/time/entries/", "/time/entries/new/", "/time/timesheets/",
    "/monitoring/", "/monitoring/feed/",
    "/screenshots/", "/screenshots/timeline/",
    "/productivity/", "/productivity/records/", "/productivity/leaderboard/",
    "/projects/", "/projects/new/", "/projects/clients/",
    "/tasks/", "/tasks/board/", "/tasks/new/",
    "/payroll/", "/payroll/periods/", "/payroll/periods/new/",
    "/notifications/", "/notifications/preferences/", "/notifications/announcements/",
    "/audit/", "/reports/", "/reports/builder/",
    "/analytics/", "/analytics/workforce/",
    "/settings/", "/settings/company/", "/settings/working-hours/",
    "/settings/leave-types/", "/settings/productivity-rules/", "/settings/holidays/",
    "/accounts/profile/", "/accounts/security/", "/accounts/change-password/",
    "/healthz/",
]

ok, bad = 0, 0
for p in paths:
    try:
        r = c.get(p)
        flag = "OK " if r.status_code in (200, 302) else "BAD"
        if r.status_code in (200, 302):
            ok += 1
        else:
            bad += 1
        print(f"{flag} {r.status_code} {p}")
    except Exception as e:  # noqa: BLE001
        bad += 1
        print(f"ERR --- {p} :: {type(e).__name__}: {str(e)[:160]}")

print(f"\nSUMMARY: {ok} ok, {bad} problems out of {len(paths)}")
