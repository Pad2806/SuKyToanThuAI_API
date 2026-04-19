from supabase import create_client, Client
from app.core.config import get_settings

settings = get_settings()

def get_supabase_client() -> Client:
    """
    Khởi tạo connection client với Supabase DB.
    Được dùng dưới dạnh Dependency Injection trong FastAPI.
    """
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    
    if not url or not key:
        raise ValueError("🚨 Thiếu cấu hình SUPABASE_URL hoặc SUPABASE_KEY trong file .env")
        
    return create_client(url, key)
