from fastapi import FastAPI
from app.routes import router
from app.middleware import ResponseTimeLoggerMiddleware
from app.metrics import start_metrics_server

app = FastAPI()

# Register middleware for logging response time
app.add_middleware(ResponseTimeLoggerMiddleware)

# Include your API routes
app.include_router(router)

# Start Prometheus metrics background collector
start_metrics_server()

# Optional health check
@app.get("/ping")
def ping():
    return {"message": "auth service is alive"}
