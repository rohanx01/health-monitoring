from fastapi import FastAPI
from app.routes import router
from app.middleware import ResponseTimeLoggerMiddleware
from app.metrics import start_metrics_server

app = FastAPI()

app.add_middleware(ResponseTimeLoggerMiddleware)
app.include_router(router)

start_metrics_server()

@app.get("/ping")
async def ping():
    return {"message": "order service is alive"}
