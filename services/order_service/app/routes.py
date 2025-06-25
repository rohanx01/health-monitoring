from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from utils.auth import verify_token
import os
import httpx
from bson import ObjectId

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

CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://catalog_service:8000")  # Adjust port & host in Docker

@router.post("/order")
async def create_order(
    data: OrderCreateModel,
    user=Depends(verify_token)
):
    # 1. Check stock from catalog_service by ID
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{CATALOG_SERVICE_URL}/product_by_id", params={"id": data.item_id})
            resp.raise_for_status()
            product = resp.json()
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Product not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Catalog service error")

    # 2. Check stock
    if product["stock"] < data.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    # 3. Create the order
    order = {
        "user_email": user["email"],
        "item_id": data.item_id,
        "quantity": data.quantity,
        "created_at": datetime.now(timezone.utc),
        "status": "placed"
    }

    try:
        result = await orders_collection.insert_one(order)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create order")

    # 4. Decrease stock in catalog_service
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{CATALOG_SERVICE_URL}/update_stock", json={
                "product_id": data.item_id,
                "quantity": data.quantity
            })
    except Exception:
        # Rollback order
        await orders_collection.delete_one({"_id": result.inserted_id})
        raise HTTPException(status_code=500, detail="Failed to update stock")

    return {"status": "success", "order_id": str(result.inserted_id)}



@router.get("/orders")
async def get_user_orders(user=Depends(verify_token)):  # ✅ No email param
    cursor = orders_collection.find({"user_email": user["email"]})
    orders = []
    async for order in cursor:
        order["_id"] = str(order["_id"])
        orders.append(order)
    return {"orders": orders}
