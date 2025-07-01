import time
import logging
import json
import os
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Histogram
from .metrics import record_http_request, record_error

# Ensure logs directory exists
os.makedirs("/app/logs", exist_ok=True)

# Configure structured logging to shared log file
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.FileHandler("/app/logs/metrics.log", mode='a'), logging.StreamHandler()]
)

# Prometheus histogram for response time in milliseconds
RESPONSE_TIME_HISTOGRAM = Histogram(
    "response_time_ms",
    "Response time per endpoint in milliseconds",
    ["method", "endpoint", "status_code"],
    buckets=[10, 25, 50, 100, 200, 300, 400, 500, 1000, 2000, 5000]
)

class ResponseTimeLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        # Extract request details
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        # Process request
        try:
            response = await call_next(request)
            process_time_ms = (time.time() - start_time) * 1000
            # Record metrics
            RESPONSE_TIME_HISTOGRAM.labels(
                method=method,
                endpoint=path,
                status_code=response.status_code
            ).observe(process_time_ms)
            # Record HTTP request metric
            record_http_request(method, path, response.status_code, time.time() - start_time)
            # Structured log for successful requests or errors
            log_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "service": "auth_service",
                "method": method,
                "path": path,
                "status_code": response.status_code,
                "latency_ms": round(process_time_ms, 2),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "request_id": request.headers.get("x-request-id", "unknown"),
            }
            if response.status_code >= 400:
                log_data["level"] = "ERROR"
                log_data["message"] = f"Request failed with status {response.status_code}"
                logging.error(json.dumps(log_data))
                for handler in logging.getLogger().handlers:
                    handler.flush()
            else:
                log_data["level"] = "INFO"
                log_data["message"] = f"Request processed successfully"
                logging.info(json.dumps(log_data))
                for handler in logging.getLogger().handlers:
                    handler.flush()
            # Add response headers for tracing
            response.headers["X-Response-Time"] = f"{process_time_ms:.2f}ms"
            response.headers["X-Request-ID"] = request.headers.get("x-request-id", "unknown")
            return response
        except Exception as e:
            process_time_ms = (time.time() - start_time) * 1000
            # Record error metrics
            record_error("request_failed", "auth_service")
            record_http_request(method, path, 500, time.time() - start_time)
            # Structured log for failed requests
            log_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "ERROR",
                "service": "auth_service",
                "method": method,
                "path": path,
                "status_code": 500,
                "latency_ms": round(process_time_ms, 2),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "request_id": request.headers.get("x-request-id", "unknown"),
                "error": str(e),
                "error_type": type(e).__name__,
                "message": f"Request failed: {str(e)}"
            }
            logging.error(json.dumps(log_data))
            for handler in logging.getLogger().handlers:
                handler.flush()
            raise

        # Optional: Save to MongoDB
        # metrics_db.service_metrics.insert_one(log_data)