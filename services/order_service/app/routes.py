from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.order_service
orders_collection = db.orders

try:
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print("❌ MongoDB connection failed:", e)


# --- Models ---
class OrderCreateModel(BaseModel):
    user_email: EmailStr
    item_id: str
    quantity: int


# --- Endpoints ---

@router.post("/order")
async def create_order(data: OrderCreateModel):
    order = {
        "user_email": data.user_email,
        "item_id": data.item_id,
        "quantity": data.quantity,
        "created_at": datetime.now(timezone.utc),
        "status": "placed"
    }
    try:
        result = await orders_collection.insert_one(order)
        return {"status": "success", "order_id": str(result.inserted_id)}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create order")


@router.get("/orders/{user_email}")
async def get_user_orders(user_email: str):
    cursor = orders_collection.find({"user_email": user_email})
    orders = []
    async for order in cursor:
        order["_id"] = str(order["_id"])
        orders.append(order)
    return {"orders": orders}
