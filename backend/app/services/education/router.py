from fastapi import APIRouter

router = APIRouter()

# 🎓 Người 4: Education Service

@router.post("/quiz")
async def generate_quiz():
    return {"msg": "Sinh / Submit quiz (Nguoi 4)"}

@router.post("/flashcard")
async def generate_flashcard():
    return {"msg": "Sinh / Interact flashcard (Nguoi 4)"}

@router.get("/history")
async def get_study_history():
    return {"msg": "Lấy kết quả lưu của user (Nguoi 4)"}
