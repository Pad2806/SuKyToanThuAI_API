from fastapi import FastAPI

app = FastAPI(title="Workspace Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/workspace/projects")
def create_project(): return {"msg": "Projects"}

@app.get("/api/v1/workspace/projects")
def list_projects(): return {"msg": "List projects"}

@app.get("/api/v1/workspace/projects/{id}")
def get_project(id: str): return {"msg": "Get project"}

@app.post("/api/v1/workspace/export/pptx")
def export_pptx(): return {"msg": "Export pptx"}

@app.post("/api/v1/workspace/export/pdf")
def export_pdf(): return {"msg": "Export pdf"}

