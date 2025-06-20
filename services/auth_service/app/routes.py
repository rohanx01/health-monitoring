from fastapi import APIRouter

router = APIRouter()

@router.post("/register")
def register_user():
    # Simulate some business logic
    return {"status": "success", "msg": "User registered"}
