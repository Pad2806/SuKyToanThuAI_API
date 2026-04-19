from fastapi import APIRouter

router = APIRouter()

# 🗂️ Người 5: Workspace & Export Service

@router.post("/projects")
async def create_project():
    return {"msg": "Create workspace project (Nguoi 5)"}

@router.get("/projects")
async def list_projects():
    return {"msg": "List workspace projects (Nguoi 5)"}

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    return {"msg": f"Get project {project_id} details (lưu content, slides, images) (Nguoi 5)"}

@router.post("/export/pptx")
async def export_pptx():
    return {"msg": "Export project to PPTX dùng python-pptx (Nguoi 5)"}

@router.post("/export/pdf")
async def export_pdf():
    return {"msg": "Export project to PDF (Nguoi 5)"}
