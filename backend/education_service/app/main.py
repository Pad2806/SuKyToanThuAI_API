from fastapi import FastAPI

app = FastAPI(title="Education Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/education/quiz")
def quiz(): return {"msg": "Quiz"}

@app.post("/api/v1/education/flashcard")
def flashcard(): return {"msg": "Flashcard"}

@app.get("/api/v1/education/history")
def history(): return {"msg": "History"}

