import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Histogram

# Optional: MongoDB logging setup
# from pymongo import MongoClient
# mongo_client = MongoClient("mongodb://mongo:27017")
# metrics_db = mongo_client.monitoring

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Prometheus histogram for response time in milliseconds
RESPONSE_TIME_HISTOGRAM = Histogram(
    "response_time_ms",
    "Response time per endpoint in milliseconds",
    ["method", "endpoint"],
    buckets=[50, 100, 200, 300, 400, 500, 1000, float("inf")]
)

class ResponseTimeLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time_ms = (time.time() - start_time) * 1000  # Convert to ms

        # Prometheus: Observe latency
        RESPONSE_TIME_HISTOGRAM.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time_ms)

        # Log to console
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(process_time_ms, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        logging.info(f"[Request] {log_data}")

        # Optional: Save to MongoDB
        # metrics_db.service_metrics.insert_one(log_data)

        return response
