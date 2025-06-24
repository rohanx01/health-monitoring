from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import bcrypt
import os
import asyncio
from jose import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "mysecretkey")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 60


router = APIRouter()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.auth_service
users_collection = db.user_metrics


try:
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

db = client.auth_service
users_collection = db.user_metrics

async def hash_password(password: str) -> bytes:
    return await asyncio.to_thread(bcrypt.hashpw, password.encode('utf-8'), bcrypt.gensalt())

async def verify_password(password: str, hashed: bytes) -> bool:
    return await asyncio.to_thread(bcrypt.checkpw, password.encode('utf-8'), hashed)


# Input schemas
class RegisterModel(BaseModel):
    email: EmailStr
    password: str

class SignInModel(BaseModel):
    email: EmailStr
    password: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register")
async def register_user(data: RegisterModel):
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = await hash_password(data.password)

    try:
        await users_collection.insert_one({
            "email": data.email,
            "passwordHash": hashed_pw,
            "sessionCount": 0,
            "createdAt": datetime.now(timezone.utc),
            "lastLoginAt": None
        })
    except Exception:
        raise HTTPException(status_code=500, detail="Database insert failed")

    return {"status": "success", "msg": "User registered"}


@router.post("/signin")
async def signin_user(data: SignInModel):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_ok = await verify_password(data.password, user["passwordHash"])
    if not password_ok:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        await users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$inc": {"sessionCount": 1},
                "$set": {"lastLoginAt": datetime.now(timezone.utc)}
            }
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Database update failed")

    token = create_access_token({"email": data.email})
    return {"status": "success", "access_token": token}

