"""Gunicorn configuration for the Remote Worker Tracker System."""
import multiprocessing
import os

# Bind to all interfaces on port 8000 (behind Nginx).
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# Worker processes: 2 * CPU + 1 is a good starting point.
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
threads = int(os.environ.get("GUNICORN_THREADS", 2))

# Recycle workers periodically to bound memory growth.
max_requests = 1000
max_requests_jitter = 100

# Timeouts.
timeout = 60
graceful_timeout = 30
keepalive = 5

# Logging to stdout/stderr (captured by the container runtime).
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

# Respect X-Forwarded-* from the Nginx proxy.
forwarded_allow_ips = "*"
proxy_protocol = False

# Process naming.
proc_name = "rwt-gunicorn"
