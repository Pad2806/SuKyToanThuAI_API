from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

from core.config import settings

security = HTTPBearer()

# ==================== CLIENTS ====================
def get_supabase_client() -> Client:
    """Client dùng cho đăng ký, đăng nhập"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def get_supabase_admin() -> Client:
    """Client dùng cho admin operations (bypass RLS)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

# ==================== MIDDLEWARE ====================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
):
    """Middleware verify JWT Token - Dùng cho tất cả protected routes"""
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        return response.user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn"
        )

async def get_current_user_profile(
    current_user = Depends(get_current_user),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """Lấy thông tin đầy đủ từ bảng users"""
    result = supabase_admin.table("users").select("*").eq("id", current_user.id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin người dùng")
    
    profile = result.data[0]
    return {**current_user.model_dump(), **profile}

async def get_current_admin(
    current_user_profile = Depends(get_current_user_profile)
):
    """Chỉ cho phép admin"""
    if current_user_profile.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập (Admin only)"
        )
    return current_user_profile