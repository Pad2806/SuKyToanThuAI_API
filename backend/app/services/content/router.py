from fastapi import APIRouter

router = APIRouter()

# 🧠 Người 2: Content Service ("Não AI text")

@router.post("/moderate")
async def moderate_content():
    return {"msg": "Kiểm duyệt nội dung (Nguoi 2)"}

@router.post("/enhance")
async def enhance_content():
    return {"msg": "Làm mượt nội dung (Nguoi 2)"}

@router.get("/keywords")
async def extract_keywords():
    return {"msg": "Trích xuất keyword (Nguoi 2)"}

@router.post("/outline")
async def generate_outline():
    return {"msg": "Sinh outline slide/comic (Nguoi 2)"}

@router.post("/regenerate")
async def regenerate_content():
    """
    Input: slides, style, tone.
    Output: nội dung mới theo ý user.
    """
    return {"msg": "Regenerate based on user edits (Nguoi 2)"}
