from fastapi import APIRouter

router = APIRouter()

# 🖼️ Người 3: Media Service (Visual AI)

@router.post("/generate-assets")
async def generate_media_assets():
    """
    Input: scenes, style, tone. 
    Output: danh sách keyword, search filter, image links
    """
    return {"msg": "Generate assets via Visual AI / Wikimedia (Nguoi 3)"}

@router.post("/regenerate-image")
async def regenerate_image():
    """Regenerate a specific image."""
    return {"msg": "Regenerate image khi user không ưng (Nguoi 3)"}
