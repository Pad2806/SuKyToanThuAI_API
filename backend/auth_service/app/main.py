from fastapi import FastAPI

app = FastAPI(title="Auth Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/auth/register", tags=["User Endpoints"])
def register(): return {"msg": "Register"}

@app.post("/api/v1/auth/login", tags=["User Endpoints"])
def login(): return {"msg": "Login"}

@app.get("/api/v1/auth/me", tags=["User Endpoints"])
def me(): return {"msg": "Me"}

# ==========================================
# 🛑 ADMIN ENDPOINTS
# ==========================================
@app.get("/api/v1/auth/admin/users", tags=["Admin Endpoints"])
def admin_list_users():
    """Lấy danh sách tất cả người dùng trong hệ thống (Pagination)"""
    return {"msg": "Admin: Lấy danh sách Users"}

@app.delete("/api/v1/auth/admin/users/{user_id}", tags=["Admin Endpoints"])
def admin_delete_user(user_id: str):
    """Xóa / Ban một user cụ thể"""
    return {"msg": f"Admin: Đã khóa / xóa User {user_id}"}
