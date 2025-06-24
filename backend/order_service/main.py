import time
import random
import os
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from loguru import logger
import psutil
import asyncio
import sys
# --- Configuration ---
# Define the port for this service. Each service will have a unique port.
PORT = 8001
SERVICE_NAME = "order-service"

# --- Logger Setup ---
# This is a crucial step. We are configuring Loguru to create structured JSON logs.
# This makes them machine-readable, which is essential for our monitoring engine.

# Ensure the logs directory exists
os.makedirs("logs", exist_ok=True)

# Remove default logger and add a new one
logger.remove()
os.makedirs("logs", exist_ok=True)
logger.add(
    f"logs/{SERVICE_NAME}.log",
    serialize=True,
    level="INFO",
    rotation="10 MB",
    retention="7 days"
)

# ALSO log to the console for live Docker logs
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)
# --- FastAPI App Initialization ---
app = FastAPI()

# --- Middleware for Logging ---
# A middleware is a function that runs for EVERY request. This is the perfect place
# to log common data like response time, CPU, and memory without repeating code.
# In each of your 3 service files (main.py), replace the old middleware with this one.

@app.middleware("http")
async def log_middleware(request: Request, call_next):
    start_time = time.time()
    
    cpu_before = psutil.cpu_percent(interval=None)
    mem_before = psutil.virtual_memory().percent
    
    # Default status code
    status_code = 500

    try:
        # Process the request
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        # If any exception occurs in the endpoint, we catch it here
        # and re-raise it after logging.
        raise e
    finally:
        # This 'finally' block ensures that logging happens NO MATTER WHAT.
        process_time = time.time() - start_time
        cpu_after = psutil.cpu_percent(interval=None)
        mem_after = psutil.virtual_memory().percent
        
        log_details = {
            "service": SERVICE_NAME,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code, # Use the captured status code
            "process_time_ms": round(process_time * 1000, 2),
            "cpu_usage_percent": round((cpu_before + cpu_after) / 2, 2),
            "memory_usage_percent": round((mem_before + mem_after) / 2, 2),
        }
        # Use a different message for errors vs success
        if status_code >= 400:
            logger.bind(json=log_details).error("Request failed")
        else:
            logger.bind(json=log_details).info("Request processed successfully")

    # This will not be reached if an exception is raised, which is fine
    # because FastAPI handles sending the final error response.
    # We return the response only on success.
    # Note: A more complex middleware might create a generic error response here.
    # For our purpose, letting the original exception propagate is sufficient.
    if 'response' in locals():
        return response
# --- API Endpoints ---
@app.post("/place-order")
async def place_order():
    """Simulates placing an order, which can sometimes fail."""
    # Simulate a 10% chance of failure (e.g., payment failed)
    if random.random() < 0.1:
        # Gather the same log details as in the middleware for error logs
        cpu_before = psutil.cpu_percent(interval=None)
        mem_before = psutil.virtual_memory().percent
        process_time = 0  # Not measured here, but required for structure
        log_details = {
            "service": SERVICE_NAME,
            "method": "POST",
            "path": "/place-order",
            "status_code": 500,
            "process_time_ms": process_time,
            "cpu_usage_percent": cpu_before,
            "memory_usage_percent": mem_before,
        }
        logger.bind(json=log_details).error(f"Payment processing failed for {SERVICE_NAME}")
        raise HTTPException(status_code=500, detail="Payment provider error")
    
    await asyncio.sleep(random.uniform(0.3, 0.6))
    return {"status": "success", "order_id": f"ORD-{random.randint(1000, 9999)}"}

@app.get("/orders/{order_id}")
async def get_order_status(order_id: str):
    """Simulates checking an order's status."""
    await asyncio.sleep(random.uniform(0.1, 0.2))
    return {"order_id": order_id, "status": random.choice(["processing", "shipped", "delivered"])}
# --- Main execution block ---
# This allows you to run the service directly using `python product_service/main.py`
if __name__ == "__main__":
    logger.info(f"Starting {SERVICE_NAME} on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)