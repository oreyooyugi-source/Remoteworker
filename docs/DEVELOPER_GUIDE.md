# Developer Guide

## Getting set up

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on *nix)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Default settings module is `config.settings.development` (see `manage.py`).

## Repository layout & conventions

- Applications live under `apps/` and are imported as `apps.<name>`.
- Each app uses the standard Django file set plus a **`services.py`** for business
  logic. Keep views thin; put logic in services so it is unit-testable.
- Shared building blocks are in `apps/core/` (base models, mixins, permissions,
  utils, validators, template tags, the custom admin site).
- Templates are project-level in `templates/<app>/…`; reuse
  `templates/partials/` (form fields, pagination, messages, sidebar, topbar).

### Coding standards

- **PEP 8**, `from __future__ import annotations`, type hints and docstrings.
- Prefer explicit querysets with `select_related` / `prefetch_related`.
- Never build SQL by string concatenation — always use the ORM.
- Add DB indexes for new hot query paths.

## Base model classes (`apps/core/models.py`)

| Base | Adds |
|------|------|
| `TimeStampedModel` | `created_at`, `updated_at` |
| `UUIDModel` | public `uuid` |
| `SoftDeleteModel` | `is_deleted`, `deleted_at`, soft-delete manager |
| `AuditableModel` | `created_by`, `updated_by` |
| `BaseModel` | timestamps + uuid |
| `FullBaseModel` | everything above |

## Permissions

- Helpers: `apps/core/permissions.py` (`is_admin`, `is_manager`, `is_hr`,
  `can_access_module`, `can_view_employee`, …).
- CBV mixins: `RoleRequiredMixin`, `AdminRequiredMixin`, `ManagerRequiredMixin`,
  `HRRequiredMixin`, `ModuleAccessMixin`.
- FBV decorators: `@role_required(...)`, `@module_required("...")`,
  `@admin_required`, `@ajax_required`.

## Auditing

Call `apps.audit.services.log(action, target=…, module=…, description=…)` from
anywhere — actor, IP and request path are pulled from thread-local state set by
`AuditLogMiddleware`. Login/logout/failed-login are logged automatically via
auth signals.

## Notifications

`apps.notifications.services.notify(user, title, message, notification_type=…,
url=…)` respects each recipient's preferences and can also send email. Use
`notify_many` / `notify_role` for broadcasts.

## Adding a new app

```bash
mkdir apps/newthing && cd apps/newthing
# create __init__.py, apps.py (AppConfig), models.py, views.py, urls.py,
# forms.py, admin.py, services.py, tests.py, migrations/__init__.py
```

1. Add `"apps.newthing"` to `LOCAL_APPS` in `config/settings/base.py`.
2. Include its URLconf in `config/urls.py` with a namespace.
3. Register admin models against the shared site:
   `from apps.core.admin import admin_site` → `@admin.register(Model, site=admin_site)`.
4. Add a nav entry in `apps/core/context_processors.navigation` and a module key
   in `ROLE_MODULE_ACCESS`.
5. `makemigrations` → `migrate` → write tests.

## Testing

```bash
python manage.py test                 # all apps (61+ tests)
python manage.py test apps.tasks      # one app
coverage run manage.py test && coverage html
python manage.py shell -c "exec(open('scripts/smoke.py').read())"   # page smoke test
```

Tests run with `DEBUG=False` and a fast password hasher. Static files use the
plain storage in dev/test; the hashed manifest storage is production-only.

## Front-end

- No build step. Bootstrap 5, Font Awesome, Chart.js and HTMX are loaded from a
  CDN in `base.html`.
- Theme variables live in `static/css/app.css` (`[data-theme="light|dark"]`).
- `static/js/app.js` initialises theme, sidebar, toasts, confirm dialogs, the
  attendance clock, the time-tracking timer and Kanban drag-and-drop.
- Pass data to Chart.js with `{{ my_dict|json_script:"id" }}` and read it in
  `static/js/charts.js`.

## Useful management commands

| Command | Purpose |
|---------|---------|
| `seed_data` | Generate demo data |
| `purge_screenshots` | Enforce screenshot retention |
| `recompute_productivity` | Rebuild scorecards |
| `backup_db` | Database + media backup |

## Gotchas

- The custom user model is `accounts.User` (`AUTH_USER_MODEL`) — always reference
  it via `get_user_model()` or `settings.AUTH_USER_MODEL`.
- The `User.timezone` field shadows the `timezone` module inside the class body;
  use the module elsewhere.
- The custom admin site is `apps.core.admin.admin_site`; register there, not on
  `django.contrib.admin.site`.
