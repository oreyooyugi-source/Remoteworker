# Administrator Manual

This guide is for Company Admins, HR Managers and Super Admins.

## Roles & access

RWT ships with ten roles. Access to each module is governed by the permission
matrix in `apps/core/permissions.py` (`ROLE_MODULE_ACCESS`).

| Role | Typical responsibilities |
|------|--------------------------|
| Super Admin | Full system control, multi-company oversight |
| Company Admin | Full control within the company |
| HR Manager | Employees, attendance, leave, payroll, reports |
| Department Manager | Their department's people, projects & productivity |
| Project Manager | Projects, tasks, timesheets |
| Supervisor / Team Lead | Team attendance, tasks, monitoring |
| Employee | Self-service |
| Auditor | Audit log, reports, analytics |
| Read-only | Dashboards & reports only |

Assign roles when creating a user (Admin panel → Users) or by editing an
employee's linked account.

## Onboarding employees

1. **Employees → Add Employee** (HR only).
2. Enter the person's name and work email, then their department, team, job
   title and employment details.
3. Save. A linked login account is created automatically; the employee sets their
   password via the reset link (or you can set one in the Admin panel).

Add HR records (documents, contracts, devices, bank/tax/salary) from the
employee's profile or the Django Admin panel.

## Company configuration (Settings)

**Settings** (admins only) centralises configuration:

- **Company** — name, branding, logo, colours, currency, timezone, and toggles
  for screenshots, activity tracking, idle threshold, GPS validation and security
  policy (2FA enforcement, password expiry, session timeout, lockout threshold).
- **Working Hours** — define standard/flex/shift policies.
- **Leave Types** — annual, sick, unpaid, parental, etc., with day allowances.
- **Productivity Rules** — classify apps/websites as productive, neutral or
  unproductive; these drive productivity scoring.
- **Holiday Calendar** — company holidays per year.

## Approvals

- **Leave** — managers approve/reject from **Attendance → Leave Requests**.
- **Timesheets** — managers approve/reject from **Timesheets**.
- **Attendance corrections** — review employee correction requests.

## Payroll

1. **Payroll → New Period** — name it and set the date range.
2. Open the period and click **Run Payroll** to generate payslips for every
   active employee (base salary, overtime, bonuses/allowances, a progressive tax
   estimate and deductions are calculated automatically).
3. Review payslips, then **Mark Paid** to finalise.

Employees can view their own payslips; only HR/Admins see everyone's.

## Monitoring & screenshots

- **Live Monitoring** — real-time view of who is working, idle, on break, in a
  meeting or offline, refreshing automatically.
- **Employee monitor** — per-person active vs idle time, top apps and websites.
- **Screenshots** — browse, filter, view a per-day timeline, flag suspicious
  captures and delete. Retention is enforced by `purge_screenshots`.

Configure capture interval, blur and retention under **Settings → Company**.

## Reports & analytics

- **Reports** — generate Employee, Department, Attendance, Productivity,
  Timesheet, Project, Payroll and Audit reports as **CSV, Excel or PDF**.
- **Analytics** — company KPIs, attendance trends, department productivity,
  headcount distribution, hours logged and a productivity forecast.

## Audit log

Every significant action (create/update/delete, login/logout, exports, approvals,
permission changes) is recorded in an **append-only** audit log. Filter by action,
module or actor. Entries cannot be edited.

## The Django Admin panel

`/admin/` provides a branded, advanced interface for power users: bulk actions,
inline editing, filters, search and a statistics view at `/admin/insights/`.

## Housekeeping

| Task | Command |
|------|---------|
| Seed demo data | `python manage.py seed_data --employees 50 --days 30` |
| Purge old screenshots | `python manage.py purge_screenshots --days 90` |
| Recompute productivity | `python manage.py recompute_productivity --days 7` |
| Backup | `python manage.py backup_db` or `deploy/backup.sh` |
