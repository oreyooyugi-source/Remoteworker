# Deployment Guide

This guide covers running the Remote Worker Tracker System in production. Two
paths are documented: **Docker Compose** (recommended) and a **manual**
Gunicorn + Nginx install.

---

## 1. Prerequisites

- A Linux host (or any Docker host) with a domain name pointing to it.
- Docker & Docker Compose **or** Python 3.12+, Nginx and a process supervisor.
- Outbound SMTP credentials for real email (optional).

---

## 2. Environment configuration

Copy the sample environment file and edit it:

```bash
cp .env.example .env
```

Set at minimum:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<generate a new 50-char random key>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
SECURE_SSL_REDIRECT=True

# Email (production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<secret>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Remote Worker Tracker <no-reply@your-domain.com>
```

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

> **Never** deploy with `DEBUG=True` or the demo `SECRET_KEY`.

---

## 3. Deploy with Docker Compose (recommended)

```bash
cd deploy
docker compose up --build -d
```

This starts:
- **web** — Django + Gunicorn (runs migrations & collectstatic on boot via
  `entrypoint.sh`).
- **nginx** — reverse proxy serving `/static/` and `/media/` and forwarding the
  rest to Gunicorn on port 80.

Create the first administrator (or set `DJANGO_SUPERUSER_*` env vars to automate):

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_data --employees 50   # optional demo data
```

Browse to `http://your-domain.com/`.

### Enabling HTTPS

Terminate TLS at Nginx (uncomment the `443` server block in `deploy/nginx.conf`
and mount certificates) or place the stack behind a TLS-terminating load
balancer / Cloudflare. When TLS terminates upstream, keep
`SECURE_PROXY_SSL_HEADER` (already set in `production.py`).

---

## 4. Manual deployment (Gunicorn + Nginx)

```bash
# 1. System packages
sudo apt update && sudo apt install -y python3.12 python3.12-venv nginx

# 2. App user & code
sudo useradd -m -d /opt/rwt rwt
sudo -u rwt -H bash -c '
  cd /opt/rwt && git clone <repo> app && cd app
  python3.12 -m venv .venv && . .venv/bin/activate
  pip install -r requirements.txt gunicorn
  cp .env.example .env   # then edit
  export DJANGO_SETTINGS_MODULE=config.settings.production
  python manage.py migrate
  python manage.py collectstatic --noinput
  python manage.py createsuperuser
'
```

### systemd service (`/etc/systemd/system/rwt.service`)

```ini
[Unit]
Description=Remote Worker Tracker (Gunicorn)
After=network.target

[Service]
User=rwt
Group=rwt
WorkingDirectory=/opt/rwt/app
EnvironmentFile=/opt/rwt/app/.env
ExecStart=/opt/rwt/app/.venv/bin/gunicorn config.wsgi:application -c deploy/gunicorn.conf.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now rwt
```

Point Nginx at the app using `deploy/nginx.conf` as a template (adjust the
`upstream` to `127.0.0.1:8000` and the `alias` paths to your `STATIC_ROOT` /
`MEDIA_ROOT`).

---

## 5. Scheduled maintenance (cron)

```cron
# Nightly database + media backup at 02:00
0 2 * * *  /opt/rwt/app/deploy/backup.sh

# Purge expired screenshots weekly
0 3 * * 0  cd /opt/rwt/app && .venv/bin/python manage.py purge_screenshots

# Recompute yesterday's productivity each morning
30 1 * * *  cd /opt/rwt/app && .venv/bin/python manage.py recompute_productivity --days 1
```

---

## 6. Backup & restore

```bash
# Backup (also available as: python manage.py backup_db)
./deploy/backup.sh /var/backups/rwt

# Restore
./deploy/restore.sh /var/backups/rwt/db_20260101_020000.sqlite3 \
                    /var/backups/rwt/media_20260101_020000.tar.gz
```

---

## 7. Production checklist

- [ ] `DEBUG=False`, unique `SECRET_KEY`, correct `ALLOWED_HOSTS`
- [ ] HTTPS enforced (`SECURE_SSL_REDIRECT`, HSTS)
- [ ] Real SMTP configured and test email sent
- [ ] `collectstatic` run and static served by Nginx/WhiteNoise
- [ ] Superuser created; demo data removed if not wanted
- [ ] Automated backups scheduled and a restore tested
- [ ] Log rotation confirmed (`logs/application.log`, `logs/security.log`)
- [ ] `python manage.py check --deploy` reviewed
