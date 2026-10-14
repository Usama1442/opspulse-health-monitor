
"""
DevOps Health Monitor (Flask)

A small web app that reports the health of the machine it runs on.
It is designed so that every DevOps tool has something real to do with it:

  /               Dashboard (HTML)
  /api/status     Full system status (JSON)
  /health         Liveness check   -> used by load balancers / Kubernetes
  /ready          Readiness check  -> used by Kubernetes / deployments
  /metrics        Prometheus-style metrics (plain text)

Configuration comes from environment variables (see README), so the same
code works on your laptop, in a container, or on a server without edits.
"""

import logging
import os
import platform
import socket
import time

import psutil
from flask import Flask, Response, jsonify, render_template, request

# ---------------------------------------------------------------------------
# Configuration (environment variables with safe defaults)
# ---------------------------------------------------------------------------
APP_NAME = "DevOps Health Monitor"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")
# A metric above its threshold (in %) is reported as "warning"
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "80"))
MEMORY_THRESHOLD = float(os.getenv("MEMORY_THRESHOLD", "80"))
DISK_THRESHOLD = float(os.getenv("DISK_THRESHOLD", "85"))

START_TIME = time.time()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("health-monitor")

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------
def level_for(value, threshold):
    """Return 'ok' or 'warning' for a percentage value."""
    return "warning" if value >= threshold else "ok"


def collect_status():
    """Collect CPU, memory, disk and system info as a dictionary."""
    cpu = psutil.cpu_percent(interval=0.2)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    try:
        load1, load5, load15 = psutil.getloadavg()
    except (AttributeError, OSError):
        load1 = load5 = load15 = None

    checks = {
        "cpu": level_for(cpu, CPU_THRESHOLD),
        "memory": level_for(memory.percent, MEMORY_THRESHOLD),
        "disk": level_for(disk.percent, DISK_THRESHOLD),
    }
    overall = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "app": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "environment": APP_ENV,
            "uptime_seconds": int(time.time() - START_TIME),
        },
        "system": {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "cpu_cores": psutil.cpu_count(logical=True),
            "load_average": [load1, load5, load15],
            "boot_time": int(psutil.boot_time()),
        },
        "metrics": {
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_mb": round(memory.used / 1024 / 1024),
            "memory_total_mb": round(memory.total / 1024 / 1024),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / 1024 ** 3, 1),
            "disk_total_gb": round(disk.total / 1024 ** 3, 1),
        },
        "thresholds": {
            "cpu": CPU_THRESHOLD,
            "memory": MEMORY_THRESHOLD,
            "disk": DISK_THRESHOLD,
        },
        "checks": checks,
        "status": overall,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    return render_template(
        "index.html", app_name=APP_NAME, version=APP_VERSION, environment=APP_ENV
    )


@app.route("/api/status")
def api_status():
    return jsonify(collect_status())


@app.route("/health")
def health():
    """Liveness: 'is the process running?' Always 200 if the app is up."""
    return jsonify(status="ok", version=APP_VERSION), 200


@app.route("/ready")
def ready():
    """Readiness: 'can this instance take traffic?'
    Returns 200 normally, or 503 if the machine is badly overloaded."""
    status = collect_status()
    metrics = status["metrics"]
    overloaded = metrics["cpu_percent"] >= 95 or metrics["memory_percent"] >= 95
    if overloaded:
        return jsonify(status="not_ready", reason="resource overload"), 503
    return jsonify(status="ready"), 200


@app.route("/metrics")
def metrics():
    """Prometheus text format, so Prometheus/Grafana can scrape this app."""
    s = collect_status()
    m = s["metrics"]
    lines = [
        "# HELP app_cpu_percent CPU usage percent",
        "# TYPE app_cpu_percent gauge",
        f"app_cpu_percent {m['cpu_percent']}",
        "# HELP app_memory_percent Memory usage percent",
        "# TYPE app_memory_percent gauge",
        f"app_memory_percent {m['memory_percent']}",
        "# HELP app_disk_percent Disk usage percent",
        "# TYPE app_disk_percent gauge",
        f"app_disk_percent {m['disk_percent']}",
        "# HELP app_uptime_seconds Seconds since the app started",
        "# TYPE app_uptime_seconds counter",
        f"app_uptime_seconds {s['app']['uptime_seconds']}",
        "",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@app.after_request
def log_request(response):
    # Skip noisy probe/metrics paths so logs stay readable
    if request.path not in ("/health", "/ready", "/metrics"):
        logger.info("%s %s -> %s", request.method, request.path, response.status_code)
    return response


if __name__ == "__main__":
    logger.info("Starting %s v%s (%s) on %s:%s", APP_NAME, APP_VERSION, APP_ENV, HOST, PORT)
    app.run(host=HOST, port=PORT)
