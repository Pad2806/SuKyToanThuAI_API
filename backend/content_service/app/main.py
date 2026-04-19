from fastapi import FastAPI

app = FastAPI(title="Content Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/content/moderate", tags=["User AI Actions"])
def moderate(): return {"msg": "Moderate"}

@app.post("/api/v1/content/enhance", tags=["User AI Actions"])
def enhance(): return {"msg": "Enhance"}

@app.get("/api/v1/content/keywords", tags=["User AI Actions"])
def keywords(): return {"msg": "Keywords"}

@app.post("/api/v1/content/outline", tags=["User AI Actions"])
def outline(): return {"msg": "Outline"}

@app.post("/api/v1/content/regenerate", tags=["User AI Actions"])
def regenerate(): return {"msg": "Regenerate"}

# ==========================================
# 🛑 ADMIN ENDPOINTS (Quản trị nội dung rễ)
# ==========================================
@app.post("/api/v1/content/admin/categories", tags=["Admin Endpoints"])
def admin_create_category():
    """Tạo mới danh mục Lịch Sử"""
    return {"msg": "Admin: Create a category"}

@app.put("/api/v1/content/admin/categories/{cat_id}", tags=["Admin Endpoints"])
def admin_update_category(cat_id: str):
    """Sửa thông tin hoặc cấp độ của Danh mục"""
    return {"msg": f"Admin: Update category {cat_id}"}

@app.post("/api/v1/content/admin/events", tags=["Admin Endpoints"])
def admin_create_event():
    """Tạo mới sự kiện lịch sử (vd: Chiến dịch Điện Biên Phủ)"""
    return {"msg": "Admin: Create historical event"}

@app.put("/api/v1/content/admin/events/{event_id}", tags=["Admin Endpoints"])
def admin_update_event(event_id: str):
    """Chỉnh sửa sự kiện sẵn có do Admin ban hành"""
    return {"msg": f"Admin: Update event {event_id}"}

@app.delete("/api/v1/content/admin/events/{event_id}", tags=["Admin Endpoints"])
def admin_delete_event(event_id: str):
    """Xóa sự kiện"""
    return {"msg": f"Admin: Xóa sự kiện {event_id}"}
