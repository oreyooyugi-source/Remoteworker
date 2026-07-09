# Remote Worker Tracker System (RWT)

A complete, production-ready **enterprise workforce intelligence platform** built
with Django 5. RWT gives companies everything they need to manage a distributed
workforce: attendance, time tracking, activity & productivity monitoring,
screenshots, project & task delivery, payroll, analytics, reporting and a full
audit trail — all rendered server-side with Django templates, Bootstrap 5 and
Chart.js.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Django](https://img.shields.io/badge/django-5.x-092E20)
![License](https://img.shields.io/badge/license-Proprietary-lightgrey)

---

## ✨ Features

| Area | Highlights |
|------|-----------|
| **Authentication** | Email/username login, remember-me, password reset, email verification, 2FA (TOTP), account lockout, session timeout, login history |
| **RBAC** | 10 built-in roles, per-module permission matrix, custom roles |
| **Employees** | Rich profiles, departments, teams, branches, job titles, skills, documents, contracts, education, certifications, devices, bank/tax/salary records, org chart |
| **Attendance** | Clock in/out, breaks, shifts (incl. night), late/early detection, leave requests + approval workflow, corrections, GPS-ready |
| **Time Tracking** | Live timer, manual entries, billable/non-billable, weekly/monthly timesheets with approvals |
| **Monitoring** | Real-time presence, activity sessions, app & website usage, device telemetry (CPU/RAM/disk/battery/network), VPN & multi-monitor flags |
| **Screenshots** | Automatic/manual capture metadata, blur, flagging, timeline viewer, retention policy |
| **Productivity** | Daily scorecards (activity, focus, efficiency, attendance), trends, forecasting, leaderboards |
| **Projects & Tasks** | Clients, budgets, milestones, risks, Kanban board with drag & drop, subtasks, checklists, comments, labels, dependencies |
| **Payroll** | Pay periods, automated payslip generation, earnings/deductions, progressive tax estimate, approvals, payslip view |
| **Analytics** | Interactive dashboards, KPIs, heatmaps, trend & forecast charts |
| **Reports** | CSV, Excel (xlsx) and PDF export for 8 report types |
| **Notifications** | In-app centre, preferences, email delivery, company announcements |
| **Audit** | Immutable, append-only log of every significant action |
| **UI/UX** | Responsive enterprise UI, light/dark mode, collapsible sidebar, toasts, animations, professional palette |

---

## 🧱 Technology Stack

- **Backend:** Python 3.12+, Django 5, Django ORM, SQLite
- **Frontend:** Django Templates, HTML5, CSS3, vanilla JavaScript, Bootstrap 5, Chart.js, HTMX, Font Awesome
- **Auth/Security:** Django auth & sessions, PBKDF2, 2FA (pyotp/qrcode), CSRF/XSS/clickjacking protections, secure headers, rate-aware lockout
- **Exports:** ReportLab (PDF), openpyxl (Excel)
- **Serving:** Gunicorn + WhiteNoise (static), Nginx & Docker ready

---

## 🚀 Quick Start

```bash
# 1. Clone & enter the project
cd RemoteApp

# 2. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional — sensible defaults exist)
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux

# 5. Apply migrations
python manage.py migrate

# 6. Create an administrator
python manage.py createsuperuser

# 7. (Optional) Load realistic demo data
python manage.py seed_data --employees 40 --days 30

# 8. Run the development server
python manage.py runserver
```

Open <http://127.0.0.1:8000/> and sign in.

### Demo credentials (after `seed_data`)

| Account | Email | Password |
|---------|-------|----------|
| Administrator | `admin@rwt.local` | *(the one you set)* |
| Demo users | `first.last@rwt.local` | `Passw0rd!2026` |

---

## 📁 Project Structure

```
RemoteApp/
├── config/                 # Django project (settings, urls, wsgi, asgi)
│   └── settings/           # base / development / production
├── apps/                   # All feature applications
│   ├── core/               # Base models, mixins, admin site, utils, dashboards
│   ├── accounts/           # Custom user, auth, RBAC, 2FA, sessions
│   ├── employees/          # Profiles, departments, teams, HR records
│   ├── attendance/         # Clock in/out, shifts, breaks, leave
│   ├── timetracking/       # Timers, manual entries, timesheets
│   ├── monitoring/         # Activity sessions, app/website usage, telemetry
│   ├── screenshots/        # Screenshot capture & timeline
│   ├── productivity/       # Scoring, trends, forecasting
│   ├── projects/           # Clients, projects, milestones, risks
│   ├── tasks/              # Kanban tasks, subtasks, comments, checklists
│   ├── payroll/            # Pay periods, payslips, components
│   ├── notifications/      # In-app + email notifications, announcements
│   ├── audit/              # Immutable audit log
│   ├── reports/            # CSV/Excel/PDF report generation
│   ├── analytics/          # KPI dashboards & charts
│   └── settings_app/       # Company config & policies
├── templates/              # Project-level templates (base, partials, per app)
├── static/                 # CSS, JS, images
├── docs/                   # Architecture, deployment, user & admin guides
├── deploy/                 # Dockerfile, compose, nginx, gunicorn, scripts
├── scripts/                # Utility scripts (smoke test, backups)
├── manage.py
└── requirements.txt
```

Each app follows a clean, consistent layout: `models.py`, `views.py`, `urls.py`,
`forms.py`, `admin.py`, `services.py`, `signals.py`, `tests.py`, `migrations/`
and (where relevant) `managers.py`, `middleware.py`, `context_processors.py`,
`templatetags/` and management commands.

---

## 🔐 Roles & Permissions

| Role | Access |
|------|--------|
| Super Admin / Company Admin | Everything |
| HR Manager | Employees, attendance, payroll, reports, analytics |
| Department / Project Manager | Team, projects, tasks, monitoring, productivity, reports |
| Supervisor / Team Lead | Attendance, tasks, productivity, monitoring |
| Employee | Own dashboard, attendance, time, tasks, productivity, screenshots |
| Auditor | Audit log, reports, analytics (read-focused) |
| Read-only | Dashboards, reports, analytics |

Module access is enforced by the `ModuleAccessMixin`, `module_required`
decorator and `apps.core.permissions` helpers.

---

## 🧪 Testing

```bash
python manage.py test                    # run all tests
python manage.py test apps.attendance    # a single app

# With coverage
coverage run manage.py test
coverage report -m
coverage html        # -> htmlcov/index.html
```

A quick end-to-end smoke test of every page:

```bash
python manage.py shell -c "exec(open('scripts/smoke.py').read())"
```

---

## 🛠️ Management Commands

| Command | Description |
|---------|-------------|
| `seed_data [--employees N] [--days D] [--flush]` | Generate realistic demo data |
| `purge_screenshots [--days N]` | Delete screenshots older than the retention window |
| `recompute_productivity [--days N]` | Rebuild productivity scorecards |
| `backup_db` | Dump the database and media to `backups/` |

---

## 🚢 Deployment

Production configuration, Docker, Docker Compose, Nginx, Gunicorn and backup
scripts live in [`deploy/`](deploy/). See the
[Deployment Guide](docs/DEPLOYMENT.md) for full instructions.

```bash
# Docker (quickest path to production-like)
cd deploy
docker compose up --build
```

---

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [User Manual](docs/USER_GUIDE.md)
- [Admin Manual](docs/ADMIN_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Database & ER Diagram](docs/DATABASE.md)

---

## 🔒 Security

RWT ships hardened against the OWASP Top 10: CSRF protection, XSS escaping, ORM
parameterisation (SQL-injection safe), clickjacking headers, secure cookies &
HSTS in production, strong password validation, account lockout, full audit
logging and per-module RBAC. Never run with `DEBUG=True` or the bundled demo
`SECRET_KEY` in production.

---

## 📄 License

Proprietary — © the project owner. All rights reserved.
