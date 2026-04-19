from fastapi import FastAPI

app = FastAPI(title="Auth Service", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/v1/auth/register")
def register(): return {"msg": "Register"}

@app.post("/api/v1/auth/login")
def login(): return {"msg": "Login"}

@app.get("/api/v1/auth/me")
def me(): return {"msg": "Me"}

