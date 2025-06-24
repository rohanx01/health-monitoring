from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from app.auth import verify_token
import os

router = APIRouter()

# DB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.order_service
orders_collection = db.orders

try:
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print("❌ MongoDB connection failed:", e)


# Models
class OrderCreateModel(BaseModel):
    item_id: str
    quantity: int


# Routes
@router.post("/order")
async def create_order(
    data: OrderCreateModel,
    user=Depends(verify_token)  # ✅ Extract user from JWT
):
    order = {
        "user_email": user["email"],                # ✅ Use email from token
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


@router.get("/orders")
async def get_user_orders(user=Depends(verify_token)):  # ✅ No email param
    cursor = orders_collection.find({"user_email": user["email"]})
    orders = []
    async for order in cursor:
        order["_id"] = str(order["_id"])
        orders.append(order)
    return {"orders": orders}
