from fastapi import FastAPI

app = FastAPI(title="Media Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/media/generate-assets")
def generate_assets(): return {"msg": "Assets"}

@app.post("/api/v1/media/regenerate-image")
def regenerate_image(): return {"msg": "Regen Image"}

