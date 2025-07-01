import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx
import time
import re
import os
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
import psutil
from dateutil import parser as dateutil_parser

# Optional: pip install ollama
try:
    import ollama
except ImportError:
    ollama = None

LOG_PATH = Path("/app/logs/metrics.log")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_log_scanner())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

# Add this after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for parsed log data and detected anomalies
parsed_logs: List[Dict[str, Any]] = []
metrics_summary: Dict[str, Any] = {}
anomaly_cache: List[str] = []
prometheus_metrics: Dict[str, Any] = {}

# --- Enhanced Log Parsing ---
def parse_log_line(line: str) -> Dict[str, Any]:
    """Parse structured and unstructured log lines, normalize level and service, always set message."""
    try:
        if line.strip().startswith('{'):
            data = json.loads(line)
            # Normalize level and service
            if 'level' in data:
                data['level'] = data['level'].upper()
            # Try to infer service if missing or unknown
            if 'service' not in data or not data['service'] or data['service'].lower() == 'unknown':
                msg = data.get('message', '')
                path = data.get('path', '')
                if '/signin' in path or '/register' in path or 'auth' in msg.lower():
                    data['service'] = 'auth_service'
                elif '/order' in path or 'order' in msg.lower():
                    data['service'] = 'order_service'
                elif '/product' in path or 'catalog' in msg.lower():
                    data['service'] = 'catalog_service'
                elif 'controller' in msg.lower():
                    data['service'] = 'controller'
                else:
                    data['service'] = 'unknown'
            # Always ensure message field exists
            if 'message' not in data or not data['message']:
                # Try to use event or raw
                data['message'] = data.get('event', '') or str(data)
            return data
    except json.JSONDecodeError:
        pass
    # Fallback to regex parsing for unstructured logs
    log_pattern = re.compile(r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+) \[(?P<level>\w+)\] (?P<message>.*)")
    match = log_pattern.match(line)
    if match:
        data = match.groupdict()
        data['level'] = data.get('level', '').upper()
        msg = data.get('message', '')
        if 'auth' in msg.lower():
            data['service'] = 'auth_service'
        elif 'order' in msg.lower():
            data['service'] = 'order_service'
        elif 'catalog' in msg.lower() or 'product' in msg.lower():
            data['service'] = 'catalog_service'
        elif 'controller' in msg.lower():
            data['service'] = 'controller'
        else:
            data['service'] = 'unknown'
        # Always ensure message field exists
        if 'message' not in data or not data['message']:
            data['message'] = str(data)
        return data
    # Always set message for raw logs
    return {"raw": line, "timestamp": datetime.now().isoformat(), "level": "INFO", "service": "unknown", "message": line}

def load_logs() -> List[Dict[str, Any]]:
    """Load and parse logs from all service log files"""
    log_files = [
        Path("/app/logs/metrics.log"),  # Main log file (controller)
        Path("/app/logs/auth_service.log"),  # Auth service logs
        Path("/app/logs/catalog_service.log"),  # Catalog service logs
        Path("/app/logs/order_service.log"),  # Order service logs
    ]
    
    logs = []
    for log_file in log_files:
        if not log_file.exists():
            continue
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1']
            file_content = None
            
            for encoding in encodings:
                try:
                    with log_file.open("r", encoding=encoding) as f:
                        file_content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                print(f"Could not read {log_file} with any encoding")
                continue
                
            for line in file_content.split('\n'):
                line = line.strip()
                if line:
                    parsed = parse_log_line(line)
                    if parsed:
                        logs.append(parsed)
                        
        except Exception as e:
            print(f"Error loading logs from {log_file}: {e}")
    
    return logs

# --- Enhanced Metrics Analysis ---
def analyze_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Comprehensive log analysis with industry-standard metrics"""
    stats = {
        "total": len(logs),
        "errors": 0,
        "auth_failures": 0,
        "http_500": 0,
        "order_404": 0,
        "latencies": [],
        "last_10_errors": [],
        "error_types": {},
        "response_codes": {},
        "services": {},
        "time_series": {},
        "performance_metrics": {
            "avg_latency_ms": None,
            "min_latency_ms": None,
            "max_latency_ms": None,
            "p95_latency_ms": None,
            "p99_latency_ms": None,
            "error_rate": 0.0,
            "success_rate": 0.0
        }
    }
    
    # Time-based analysis
    current_time = datetime.now()
    time_windows = {
        "last_1h": current_time - timedelta(hours=1),
        "last_15m": current_time - timedelta(minutes=15),
        "last_5m": current_time - timedelta(minutes=5)
    }
    
    for log in logs:
        msg = log.get("message", "")
        level = log.get("level", "")
        service = log.get("service", "unknown")
        status_code = log.get("status_code")
        # Use either latency_ms or duration_ms
        latency = log.get("latency_ms")
        if latency is None:
            latency = log.get("duration_ms")
        timestamp_str = log.get("timestamp", "")
        
        # Service tracking
        if service not in stats["services"]:
            stats["services"][service] = {
                "total_requests": 0,
                "errors": 0,
                "avg_latency": 0,
                "latencies": []
            }
        
        stats["services"][service]["total_requests"] += 1
        
        # Count errors
        if "error" in msg.lower() or level == "ERROR":
            stats["errors"] += 1
            stats["services"][service]["errors"] += 1
            if len(stats["last_10_errors"]) < 10:
                stats["last_10_errors"].append(log)
        
        # Count specific error types
        if "401" in msg or "authentication failed" in msg.lower():
            stats["auth_failures"] += 1
            stats["error_types"]["auth_failure"] = stats["error_types"].get("auth_failure", 0) + 1
        if "500" in msg or (status_code and status_code == 500):
            stats["http_500"] += 1
            stats["error_types"]["http_500"] = stats["error_types"].get("http_500", 0) + 1
        if "404" in msg and "order" in msg.lower():
            stats["order_404"] += 1
            stats["error_types"]["order_404"] = stats["error_types"].get("order_404", 0) + 1
        
        # Latency analysis
        if latency is not None:
            stats["latencies"].append(latency)
            stats["services"][service]["latencies"].append(latency)
        
        # Response code analysis
        if status_code:
            stats["response_codes"][str(status_code)] = stats["response_codes"].get(str(status_code), 0) + 1
        
        # Time series analysis
        try:
            if timestamp_str:
                log_time = dateutil_parser.parse(timestamp_str)
                for window_name, window_start in time_windows.items():
                    if log_time >= window_start:
                        if window_name not in stats["time_series"]:
                            stats["time_series"][window_name] = {"total": 0, "errors": 0}
                        stats["time_series"][window_name]["total"] += 1
                        if "error" in msg.lower() or level == "ERROR":
                            stats["time_series"][window_name]["errors"] += 1
        except Exception:
            pass
    
    # Calculate performance metrics
    if stats["latencies"]:
        latencies = sorted(stats["latencies"])
        stats["performance_metrics"].update({
            "avg_latency_ms": sum(latencies) / len(latencies),
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
            "p99_latency_ms": latencies[int(len(latencies) * 0.99)]
        })
    
    # Calculate rates
    if stats["total"] > 0:
        stats["performance_metrics"]["error_rate"] = (stats["errors"] / stats["total"]) * 100
        stats["performance_metrics"]["success_rate"] = 100 - stats["performance_metrics"]["error_rate"]
    
    # Calculate service-specific metrics
    for service in stats["services"]:
        service_data = stats["services"][service]
        if service_data["latencies"]:
            service_data["avg_latency"] = sum(service_data["latencies"]) / len(service_data["latencies"])
    
    return stats

async def scrape_prometheus() -> Dict[str, Any]:
    """Enhanced Prometheus metrics scraping with industry-standard queries"""
    metrics = {}
    queries = {
        "up": "up",
        "http_requests_total": "http_requests_total",
        "http_request_duration_seconds": "http_request_duration_seconds",
        "response_time_ms": "response_time_ms",
        "cpu_percent": "cpu_percent",
        "memory_used_mb": "memory_used_mb",
        "auth_attempts_total": "auth_attempts_total",
        "jwt_tokens_issued_total": "jwt_tokens_issued_total",
        "db_operations_total": "db_operations_total",
        "errors_total": "errors_total",
        "process_start_time_seconds": "process_start_time_seconds"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Scrape individual metrics
            for metric_name, query in queries.items():
                try:
                    resp = await client.get(
                        f"{PROMETHEUS_URL}/api/v1/query", 
                        params={"query": query}, 
                        timeout=5
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        metrics[metric_name] = data.get("data", {}).get("result", [])
                    else:
                        metrics[f"{metric_name}_error"] = resp.text
                except Exception as e:
                    metrics[f"{metric_name}_error"] = str(e)
            
            # Get service health status
            resp = await client.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=5)
            if resp.status_code == 200:
                targets_data = resp.json()
                metrics["targets"] = targets_data.get("data", {}).get("activeTargets", [])
            
            # Get metric metadata
            resp = await client.get(f"{PROMETHEUS_URL}/api/v1/label/__name__/values", timeout=5)
            if resp.status_code == 200:
                metadata = resp.json()
                metrics["available_metrics"] = metadata.get("data", [])
            
    except Exception as e:
        metrics["prometheus_error"] = str(e)
    
    return metrics

# --- Enhanced Anomaly Detection ---
def detect_anomalies(logs: List[Dict[str, Any]]) -> List[str]:
    """Advanced anomaly detection with multiple algorithms"""
    anomalies = []
    
    # Check last 100 logs for anomalies
    recent_logs = logs[-100:] if len(logs) > 100 else logs
    
    # 1. Error rate anomaly
    error_count = sum(1 for log in recent_logs if log.get("level") == "ERROR")
    if error_count > 10:
        anomalies.append(f"High error rate detected: {error_count} errors in last 100 logs")
    
    # 2. HTTP 500 anomaly
    http_500_count = sum(1 for log in recent_logs if "500" in log.get("message", ""))
    if http_500_count > 5:
        anomalies.append(f"Spike in HTTP 500 errors: {http_500_count} in last 100 logs")
    
    # 3. Authentication failures anomaly
    auth_failures = sum(1 for log in recent_logs if "401" in log.get("message", ""))
    if auth_failures > 5:
        anomalies.append(f"Spike in authentication failures: {auth_failures} in last 100 logs")
    
    # 4. Latency anomaly detection
    latencies = []
    for log in recent_logs:
        latency = log.get("latency_ms")
        if latency:
            latencies.append(latency)
    
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        if avg_latency > 1000:  # More than 1 second average
            anomalies.append(f"High average latency detected: {avg_latency:.2f}ms")
        
        # Detect latency spikes (values > 2x average)
        threshold = avg_latency * 2
        spikes = [l for l in latencies if l > threshold]
        if len(spikes) > 3:
            anomalies.append(f"Latency spikes detected: {len(spikes)} requests > {threshold:.2f}ms")
    
    # 5. Service-specific anomalies
    service_errors = {}
    for log in recent_logs:
        service = log.get("service", "unknown")
        if "error" in log.get("message", "").lower() or log.get("level") == "ERROR":
            service_errors[service] = service_errors.get(service, 0) + 1
    
    for service, error_count in service_errors.items():
        if error_count > 3:
            anomalies.append(f"Service {service} has high error rate: {error_count} errors")
    
    return anomalies

# --- Enhanced Ollama Integration ---
async def ask_ollama_for_root_cause(logs: List[Dict[str, Any]], anomalies: List[str]) -> str:
    """Enhanced root cause analysis with Ollama"""
    if not ollama:
        return "Ollama client not installed. Please install: pip install ollama"
    
    # Prepare comprehensive context
    recent_logs = logs[-50:] if logs else []
    
    # Extract key information
    error_logs = [log for log in recent_logs if log.get("level") == "ERROR"]
    service_errors = {}
    for log in error_logs:
        service = log.get("service", "unknown")
        service_errors[service] = service_errors.get(service, 0) + 1
    
    # Create detailed prompt
    prompt = f"""
You are a DevOps engineer analyzing a microservices system. Please provide root cause analysis for the following issues:

ANOMALIES DETECTED:
{chr(10).join(f"- {anomaly}" for anomaly in anomalies)}

RECENT ERROR PATTERNS:
{chr(10).join(f"- {service}: {count} errors" for service, count in service_errors.items())}

SAMPLE ERROR LOGS:
{chr(10).join(f"- {log.get('message', 'No message')}" for log in error_logs[:10])}

SYSTEM CONTEXT:
- This is a microservices architecture with auth, catalog, and order services
- Services communicate via HTTP APIs with JWT authentication
- MongoDB is used for data storage
- Prometheus is used for metrics collection

Please provide:
1. Most likely root cause(s)
2. Immediate actions to take
3. Long-term recommendations
4. Monitoring improvements

Focus on actionable insights and specific recommendations.
"""
    
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL, 
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3}  # Lower temperature for more focused analysis
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Ollama error: {e}. Please ensure Ollama is running and llama3 model is available."

# --- Background Task ---
async def background_log_scanner():
    """Enhanced background log scanner with Prometheus integration"""
    global parsed_logs, metrics_summary, anomaly_cache, prometheus_metrics
    last_size = 0
    
    while True:
        try:
            # Load and parse logs
            logs = load_logs()
            if len(logs) != last_size:
                parsed_logs = logs
                metrics_summary = analyze_logs(logs)
                anomaly_cache = detect_anomalies(logs)
                last_size = len(logs)
            
            # Scrape Prometheus metrics
            prometheus_metrics = await scrape_prometheus()
            
        except Exception as e:
            print(f"Error in background scanner: {e}")
        
        await asyncio.sleep(30)  # Update every 30 seconds

# --- API Endpoints ---
@app.get("/api/summary")
async def api_summary():
    return {"summary": metrics_summary, "anomalies": anomaly_cache}

@app.get("/api/metrics")
async def api_metrics():
    return {
        "log_metrics": metrics_summary, 
        "prometheus_metrics": prometheus_metrics
    }

async def ai_incident_analysis(anomaly, logs, metrics, dependencies=None):
    """Industry-standard AI incident analysis using LLM"""
    prompt = f"""
You are an SRE. Analyze this incident:

Anomaly: {anomaly}
Recent logs:
{chr(10).join([json.dumps(log) for log in logs[-20:]])}

Recent metrics:
{json.dumps(metrics, indent=2)}

Service dependencies:
{dependencies or 'N/A'}

Please:
1. Summarize the incident.
2. Suggest the most likely root cause.
3. Recommend immediate actions.
4. Suggest long-term improvements.
"""
    if not ollama:
        return "Ollama client not installed. Please install: pip install ollama"
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2}
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Ollama error: {e}. Please ensure Ollama is running and llama3 model is available."

@app.get("/api/ai_analysis")
async def api_ai_analysis(
    time_window_minutes: int = Query(15, ge=1, le=120),
    anomaly: str = Query(None, description="Optional anomaly description")
):
    now = datetime.now()
    window_start = now - timedelta(minutes=time_window_minutes)
    logs_window = [log for log in parsed_logs if "timestamp" in log and dateutil_parser.parse(log["timestamp"]) >= window_start]
    metrics_snapshot = metrics_summary.copy() if metrics_summary else {}
    dependencies = "auth_service -> order_service -> catalog_service (example)"
    ai_result = await ai_incident_analysis(anomaly or "Manual analysis requested", logs_window, metrics_snapshot, dependencies)
    return {
        "anomaly": anomaly or "Manual analysis requested",
        "time_window_minutes": time_window_minutes,
        "log_count": len(logs_window),
        "ai_analysis": ai_result
    }

@app.get("/api/root_cause")
async def api_root_cause():
    # Always run AI analysis, even if no anomalies detected
    now = datetime.now()
    window_start = now - timedelta(minutes=15)
    logs_window = [log for log in parsed_logs if "timestamp" in log and dateutil_parser.parse(log["timestamp"]) >= window_start]
    metrics_snapshot = metrics_summary.copy() if metrics_summary else {}
    dependencies = "auth_service -> order_service -> catalog_service (example)"
    anomaly_text = "; ".join(anomaly_cache) if anomaly_cache else "No anomalies detected, manual analysis"
    ai_result = await ai_incident_analysis(anomaly_text, logs_window, metrics_snapshot, dependencies)
    return {
        "anomalies": anomaly_cache,
        "ai_analysis": ai_result
    }

@app.get("/api/health")
async def api_health():
    """Comprehensive health check endpoint"""
    prometheus_healthy = "prometheus_error" not in prometheus_metrics
    logs_healthy = len(parsed_logs) > 0
    
    # Check if services are responding
    services_healthy = True
    if "targets" in prometheus_metrics:
        for target in prometheus_metrics["targets"]:
            if target.get("health") != "up":
                services_healthy = False
                break
    
    overall_health = prometheus_healthy and logs_healthy and services_healthy
    
    return {
        "status": "healthy" if overall_health else "unhealthy",
        "components": {
            "prometheus": "healthy" if prometheus_healthy else "unhealthy",
            "logs": "healthy" if logs_healthy else "unhealthy", 
            "services": "healthy" if services_healthy else "unhealthy"
        },
        "metrics": {
            "total_logs": len(parsed_logs),
            "total_errors": metrics_summary.get("errors", 0),
            "active_anomalies": len(anomaly_cache)
        }
    }

@app.get("/api/analytics")
async def api_analytics():
    """Detailed analytics endpoint"""
    return {
        "log_analytics": {
            "total_requests": metrics_summary.get("total", 0),
            "error_rate": f"{(metrics_summary.get('errors', 0) / max(metrics_summary.get('total', 1), 1)) * 100:.2f}%",
            "error_types": metrics_summary.get("error_types", {}),
            "response_codes": metrics_summary.get("response_codes", {}),
            "latency_stats": metrics_summary.get("performance_metrics", {}),
            "services": metrics_summary.get("services", {}),
            "time_series": metrics_summary.get("time_series", {})
        },
        "anomalies": anomaly_cache,
        "recent_errors": metrics_summary.get("last_10_errors", [])
    }

@app.get("/api/prometheus/status")
async def api_prometheus_status():
    """Detailed Prometheus status and metrics"""
    return {
        "status": "healthy" if "prometheus_error" not in prometheus_metrics else "unhealthy",
        "targets": prometheus_metrics.get("targets", []),
        "available_metrics": prometheus_metrics.get("available_metrics", []),
        "metrics_summary": {
            "http_requests": len(prometheus_metrics.get("http_requests_total", [])),
            "auth_attempts": len(prometheus_metrics.get("auth_attempts_total", [])),
            "jwt_tokens": len(prometheus_metrics.get("jwt_tokens_issued_total", [])),
            "db_operations": len(prometheus_metrics.get("db_operations_total", [])),
            "errors": len(prometheus_metrics.get("errors_total", []))
        }
    }

@app.get("/api/performance")
async def api_performance():
    """Performance-focused analytics"""
    perf_metrics = metrics_summary.get("performance_metrics", {})
    return {
        "latency_analysis": {
            "average_ms": perf_metrics.get("avg_latency_ms"),
            "p95_ms": perf_metrics.get("p95_latency_ms"),
            "p99_ms": perf_metrics.get("p99_latency_ms"),
            "min_ms": perf_metrics.get("min_latency_ms"),
            "max_ms": perf_metrics.get("max_latency_ms")
        },
        "throughput": {
            "total_requests": metrics_summary.get("total", 0),
            "success_rate": f"{perf_metrics.get('success_rate', 0):.2f}%",
            "error_rate": f"{perf_metrics.get('error_rate', 0):.2f}%"
        },
        "service_performance": metrics_summary.get("services", {}),
        "time_series": metrics_summary.get("time_series", {})
    }

@app.get("/api/errors/analysis")
async def api_errors_analysis():
    """Detailed error analysis"""
    return {
        "error_summary": {
            "total_errors": metrics_summary.get("errors", 0),
            "error_types": metrics_summary.get("error_types", {}),
            "error_rate": f"{metrics_summary.get('performance_metrics', {}).get('error_rate', 0):.2f}%"
        },
        "recent_errors": metrics_summary.get("last_10_errors", []),
        "service_errors": {
            service: data.get("errors", 0) 
            for service, data in metrics_summary.get("services", {}).items()
        },
        "response_code_errors": {
            code: count for code, count in metrics_summary.get("response_codes", {}).items()
            if code.startswith("4") or code.startswith("5")
        }
    }

@app.get("/api/ollama/test")
async def api_ollama_test():
    """Test Ollama connection and model availability"""
    if not ollama:
        return {
            "status": "not_available",
            "message": "Ollama client not installed. Install with: pip install ollama"
        }
    
    try:
        # Test basic connection
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            options={"temperature": 0.1}
        )
        return {
            "status": "working",
            "model": OLLAMA_MODEL,
            "response": response["message"]["content"][:100] + "...",
            "message": "Ollama is working correctly"
        }
    except Exception as e:
        return {
            "status": "error",
            "model": OLLAMA_MODEL,
            "error": str(e),
            "message": "Ollama connection failed. Ensure Ollama is running and model is available."
        }

def tail_log_file(path: Path, n: int) -> list:
    """Efficiently read the last n lines from a file."""
    with path.open('rb') as f:
        f.seek(0, 2)
        filesize = f.tell()
        blocksize = 1024
        data = b''
        lines = []
        while len(lines) <= n and f.tell() > 0:
            seek_offset = min(f.tell(), blocksize)
            f.seek(-seek_offset, 1)
            data = f.read(seek_offset) + data
            f.seek(-seek_offset, 1)
            lines = data.split(b'\n')
        # Only keep the last n lines
        return [line.decode('utf-8', errors='replace') for line in lines[-n:] if line.strip()]

@app.get("/api/logs")
async def api_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=10000),
    level: str = Query(None),
    service: str = Query(None),
    time_start: str = Query(None),
    time_end: str = Query(None)
):
    """Efficiently stream and filter logs from disk with pagination and filtering."""
    # Read last (offset+limit) lines from the log file
    n = offset + limit
    lines = tail_log_file(LOG_PATH, n)
    logs = [parse_log_line(line) for line in lines]
    logs = logs[::-1]  # Newest first

    # Apply filters
    if level:
        logs = [log for log in logs if log.get("level", "").upper() == level.upper()]
    if service:
        logs = [log for log in logs if log.get("service", "").lower() == service.lower()]
    if time_start:
        try:
            start_dt = dateutil_parser.parse(time_start)
            logs = [log for log in logs if "timestamp" in log and dateutil_parser.parse(log["timestamp"]) >= start_dt]
        except Exception:
            pass
    if time_end:
        try:
            end_dt = dateutil_parser.parse(time_end)
            logs = [log for log in logs if "timestamp" in log and dateutil_parser.parse(log["timestamp"]) <= end_dt]
        except Exception:
            pass

    paginated_logs = logs[offset:offset+limit]
    return {
        "logs": paginated_logs,
        "total": len(logs),
        "offset": offset,
        "limit": limit,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/services")
async def api_services():
    """Return per-service metrics: uptime, avg response time, latency, memory, cpu, error rate, status"""
    service_names = ["auth_service", "catalog_service", "order_service"]
    now = datetime.now()
    service_metrics = {}
    prom_metrics = prometheus_metrics
    def get_prom_value(metric_name, service_name):
        results = prom_metrics.get(metric_name, [])
        for entry in results:
            metric = entry.get('metric', {})
            if (
                metric.get('job') == service_name or
                metric.get('service') == service_name or
                service_name in metric.get('instance', '')
            ):
                try:
                    return float(entry.get('value', [None, 0])[1])
                except Exception:
                    continue
        return 0
    for name in service_names:
        logs = [log for log in parsed_logs if log.get("service") == name]
        errors = [log for log in logs if log.get("level") == "ERROR"]
        latencies = [log.get("latency_ms") if log.get("latency_ms") is not None else log.get("duration_ms") for log in logs if log.get("latency_ms") is not None or log.get("duration_ms") is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        # Uptime: use process_start_time_seconds from Prometheus
        process_start_time = get_prom_value("process_start_time_seconds", name)
        if process_start_time > 0:
            uptime = (time.time() - process_start_time) / 60  # in minutes
        else:
            uptime = None
        mem = get_prom_value("memory_used_mb", name)
        cpu = get_prom_value("cpu_percent", name)
        service_metrics[name] = {
            "name": name,
            "displayName": name.replace("_", " ").title(),
            "status": "healthy" if len(errors) == 0 else "warning",
            "uptime": round(uptime, 2) if uptime else None,  # in minutes
            "avg_latency": round(avg_latency, 2) if avg_latency else None,
            "memory_mb": round(mem, 2),
            "cpu_percent": round(cpu, 2),
            "error_rate": round((len(errors)/max(len(logs),1))*100, 2) if logs else 0,
            "total_requests": len(logs),
            "errors": len(errors),
        }
    return {"services": list(service_metrics.values())}

@app.get("/api/debug/service-log-counts")
async def api_debug_service_log_counts():
    """Debug endpoint to check log counts per service"""
    service_counts = {}
    total_logs = len(parsed_logs)
    
    # Count logs by service
    for log in parsed_logs:
        service = log.get("service", "unknown")
        if service not in service_counts:
            service_counts[service] = {"total": 0, "errors": 0, "info": 0, "warning": 0}
        
        service_counts[service]["total"] += 1
        level = log.get("level", "").upper()
        if level == "ERROR":
            service_counts[service]["errors"] += 1
        elif level == "INFO":
            service_counts[service]["info"] += 1
        elif level == "WARNING":
            service_counts[service]["warning"] += 1
    
    # Get sample logs for each service
    sample_logs = {}
    for service in service_counts.keys():
        service_logs = [log for log in parsed_logs if log.get("service") == service]
        sample_logs[service] = service_logs[-5:] if service_logs else []  # Last 5 logs
    
    return {
        "total_logs": total_logs,
        "service_counts": service_counts,
        "sample_logs": sample_logs,
        "log_file_exists": LOG_PATH.exists(),
        "log_file_size": LOG_PATH.stat().st_size if LOG_PATH.exists() else 0,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/debug/log-sample")
async def api_debug_log_sample():
    # Return the last 20 error logs with service and level fields
    error_logs = [log for log in parsed_logs if log.get("level") == "ERROR"]
    return {"error_logs": error_logs[-20:]}

@app.get("/api/debug/service-error-counts")
async def api_debug_service_error_counts():
    # Count ERROR logs per service
    error_counts = {}
    for log in parsed_logs:
        if log.get("level") == "ERROR":
            service = log.get("service", "unknown")
            error_counts[service] = error_counts.get(service, 0) + 1
    return {"service_error_counts": error_counts}

# --- Expandable: Add more endpoints or analysis as needed --- 