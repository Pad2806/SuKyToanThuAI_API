from fastapi import APIRouter

router = APIRouter()

# 👤 Người 1: Auth Service

@router.post("/register")
async def register_user():
    return {"msg": "Register user endpoint (Nguoi 1)"}

@router.post("/login")
async def login_user():
    return {"msg": "Login user endpoint (Nguoi 1)"}

@router.get("/me")
async def get_current_user():
    return {"msg": "Get current user info (Nguoi 1)"}
