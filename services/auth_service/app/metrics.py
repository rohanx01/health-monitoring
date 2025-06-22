from prometheus_client import start_http_server, Gauge
import psutil, time, threading

# Define metrics
cpu_percent = Gauge("cpu_percent", "CPU usage percent")
memory_used = Gauge("memory_used_mb", "Used memory in MB")

def collect_metrics():
    while True:
        cpu_percent.set(psutil.cpu_percent(interval=0.1))
        memory_used.set(psutil.virtual_memory().used / 1024 / 1024)
        time.sleep(5)

def start_metrics_server():
    threading.Thread(target=collect_metrics, daemon=True).start()
    start_http_server(8002)  # expose /metrics
