from fastapi import FastAPI
from .routes import router
from .middleware import LoggingMiddleware
from .metrics import start_metrics_server
import threading

app = FastAPI(title="Catalog Service", version="1.0.0")

# Add middleware
app.add_middleware(LoggingMiddleware)

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/ping")
async def ping():
    return {"status": "healthy", "service": "catalog_service"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "catalog_service",
        "version": "1.0.0",
        "endpoints": [
            "/api/v1/all_products",
            "/api/v1/product",
            "/api/v1/product_by_id",
            "/api/v1/add_product",
            "/api/v1/update_stock"
        ]
    }

# Start metrics server in background
@app.on_event("startup")
async def startup_event():
    # Start metrics server in a separate thread
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()
    print("🚀 Catalog Service started with enhanced metrics and logging")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Catalog Service shutting down")