import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Optional: MongoDB logging setup
# from pymongo import MongoClient
# mongo_client = MongoClient("mongodb://mongo:27017")
# metrics_db = mongo_client.monitoring

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class ResponseTimeLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # ms

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": round(process_time, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Log to console
        logging.info(f"[Request] {log_data}")

        # Optional: log to MongoDB
        # metrics_db.service_metrics.insert_one(log_data)

        return response
