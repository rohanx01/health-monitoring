from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime,timezone
import bcrypt
import os

router = APIRouter()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)

try:
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

db = client.auth_service
users_collection = db.user_metrics

# Input schemas
class RegisterModel(BaseModel):
    email: EmailStr
    password: str

class SignInModel(BaseModel):
    email: EmailStr
    password: str

# POST /register
@router.post("/register")
def register_user(data: RegisterModel):
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())

    users_collection.insert_one({
        "email": data.email,
        "passwordHash": hashed_pw,
        "sessionCount": 0,
        "createdAt": datetime.now(timezone.utc),
        "lastLoginAt": None
    })

    return {"status": "success", "msg": "User registered"}

# POST /signin
@router.post("/signin")
def signin_user(data: SignInModel):
    user = users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(data.password.encode('utf-8'), user['passwordHash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update session count and last login time
    users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$inc": {"sessionCount": 1},
            "$set": {"lastLoginAt": datetime.now(timezone.utc)}
        }
    )

    return {"status": "success", "msg": "Login successful"}
