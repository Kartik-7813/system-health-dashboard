"""
System Health Monitoring Dashboard
===================================
A real-time system monitoring web application built with Python and Flask.
Tracks CPU, RAM, Disk, and Network metrics via REST API endpoints.

Tech Stack: Python, Flask, psutil, HTML, CSS, JavaScript
Author: Kartik Chinchole
"""

from flask import Flask, jsonify, render_template
import psutil
import logging
from datetime import datetime

# ── App Initialization ─────────────────────────────────────────
app = Flask(__name__)

# ── Logger Setup ───────────────────────────────────────────────
# Logs every API request with timestamp to monitor.log file
logging.basicConfig(
    filename="monitor.log",
    level=logging.INFO,
    format="%(message)s"
)

def log_request(endpoint):
    """Log each API request with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"[{timestamp}] Request → {endpoint}")


# ── Alert Thresholds ───────────────────────────────────────────
# If any metric crosses these values, alert is triggered
THRESHOLDS = {
    "cpu":    80.0,   # CPU usage above 80% = alert
    "ram":    80.0,   # RAM usage above 80% = alert
    "disk":   90.0,   # Disk usage above 90% = alert
}


def check_alert(metric_name, value):
    """
    Check if a metric has crossed its alert threshold.
    Returns a warning message if threshold exceeded, else None.
    """
    threshold = THRESHOLDS.get(metric_name)
    if threshold and value > threshold:
        return f"⚠️ {metric_name.upper()} usage is HIGH: {value}%"
    return None


# ── Helper: Get Network Speed ──────────────────────────────────
# psutil gives total bytes sent/received since system boot
# To get speed, we take two readings and compute the difference

_last_net = psutil.net_io_counters()  # first reading at startup

def get_network_speed():
    """
    Calculate current upload and download speed in MB/s.
    Uses delta between current and last reading.
    """
    global _last_net

    current_net  = psutil.net_io_counters()

    # Delta = difference between current and last reading
    bytes_sent     = current_net.bytes_sent     - _last_net.bytes_sent
    bytes_received = current_net.bytes_recv     - _last_net.bytes_recv

    # Update last reading for next call
    _last_net = current_net

    # Convert bytes to MB (1 MB = 1024 * 1024 bytes)
    upload_mb   = round(bytes_sent     / (1024 * 1024), 3)
    download_mb = round(bytes_received / (1024 * 1024), 3)

    return upload_mb, download_mb


# ── Routes ─────────────────────────────────────────────────────

@app.route("/")
def index():
    """
    Serve the main dashboard HTML page.
    Flask looks for index.html inside the templates/ folder.
    """
    return render_template("index.html")


@app.route("/api/metrics")
def get_metrics():
    """
    REST API endpoint that returns all system metrics as JSON.
    Called by the frontend every 5 seconds via JavaScript fetch().

    Returns:
        JSON with cpu, ram, disk, network, alerts, timestamp
    """
    log_request("/api/metrics")

    # ── Collect Metrics ──────────────────────────────────────
    cpu_percent  = psutil.cpu_percent(interval=1)   # CPU usage %
    ram          = psutil.virtual_memory()           # RAM info object
    disk         = psutil.disk_usage("/")            # Disk info object
    upload, download = get_network_speed()           # Network speed

    ram_percent  = ram.percent
    disk_percent = disk.percent

    # ── Check Alerts ─────────────────────────────────────────
    alerts = []
    for metric, value in [("cpu", cpu_percent), ("ram", ram_percent), ("disk", disk_percent)]:
        alert = check_alert(metric, value)
        if alert:
            alerts.append(alert)

    # ── Build Response ────────────────────────────────────────
    data = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "cpu": {
            "percent": cpu_percent,
            "cores":   psutil.cpu_count()
        },
        "ram": {
            "percent":   ram_percent,
            "used_gb":   round(ram.used   / (1024 ** 3), 2),
            "total_gb":  round(ram.total  / (1024 ** 3), 2)
        },
        "disk": {
            "percent":   disk_percent,
            "used_gb":   round(disk.used  / (1024 ** 3), 2),
            "total_gb":  round(disk.total / (1024 ** 3), 2)
        },
        "network": {
            "upload_mb":   upload,
            "download_mb": download
        },
        "alerts": alerts
    }

    return jsonify(data)


@app.route("/api/status")
def get_status():
    """
    Simple health check endpoint.
    Returns server status and uptime info.
    Useful for deployment health checks on Render.
    """
    log_request("/api/status")
    return jsonify({
        "status":    "running",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message":   "System Health Monitor is active"
    })


# ── Run App ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting System Health Monitor...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True)
