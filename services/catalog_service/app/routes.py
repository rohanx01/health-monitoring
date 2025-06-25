from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from utils.auth import verify_token  
import os
from bson import ObjectId

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.catalog_service
products_collection = db.products

class ProductResponseModel(BaseModel):
    name: str
    description: str
    stock: int

class ProductCreateModel(BaseModel):
    name: str
    description: str
    stock: int

@router.get("/product", response_model=list[ProductResponseModel])
async def get_product_by_name(
    name: str = Query(...),
    user=Depends(verify_token)  # ✅ Require valid token
):
    cursor = products_collection.find({"name": {"$regex": name, "$options": "i"}})
    products = []
    async for product in cursor:
        products.append({
            "name": product["name"],
            "description": product["description"],
            "stock": product["stock"]
        })
    if not products:
        raise HTTPException(status_code=404, detail="No products found")
    return products


class StockUpdateModel(BaseModel):
    product_name: str
    quantity: int

class StockUpdateModel(BaseModel):
    product_id: str
    quantity: int

@router.post("/update_stock")
async def update_stock(data: StockUpdateModel, user=Depends(verify_token)):
    try:
        result = await products_collection.update_one(
            {"_id": ObjectId(data.product_id), "stock": {"$gte": data.quantity}},
            {"$inc": {"stock": -data.quantity}}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID or update failed")

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Insufficient stock or product not found")

    return {"status": "stock updated"}

@router.post("/add_product")
async def add_product(data: ProductCreateModel, user=Depends(verify_token)):
    # Optional: restrict to certain users (e.g. admin only)
    # if user.get("email") != "admin@example.com":
    #     raise HTTPException(status_code=403, detail="Not authorized")

    product = {
        "name": data.name,
        "description": data.description,
        "stock": data.stock
    }

    try:
        result = await products_collection.insert_one(product)
        return {
            "status": "success",
            "product_id": str(result.inserted_id),
            "msg": "Product added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to add product")