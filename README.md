# SuKyAI API

FastAPI microservice backend for Sử Ký AI.

## Services

- `auth-service` on `8001`: JWT register, login, refresh, logout, and profile APIs.
- `content-service` on `8002`: public historical eras, events, grades, textbook, and search APIs.
- `ai-service` on `8003`: authenticated research/create MVP and user page history.
- `db-migrate`: Alembic migration runner plus seed data import.
- `redis`: token blacklist and RAG query cache.
- `nginx`: frontend static files and `/api/{auth|content|ai}` proxy.

## Quick Start

1. Copy `.env.example` to `.env`.
2. Fill `DATABASE_URL`, `JWT_SECRET_KEY`, and optional OpenAI-compatible settings.
   For Supabase on Docker Desktop, prefer the session pooler URL on port `5432`
   because direct database hosts are IPv6-only by default.
3. Start the stack: `docker compose up --build`.
4. Open `http://localhost`.

The `nginx` image builds `../SuKyAI_Web` with `VITE_API_BASE_URL=/api`, serves the
compiled frontend, and proxies `/api/{auth|content|ai}` to the backend services.

Swagger docs are available through nginx at `/api/auth/docs`, `/api/content/docs`, and `/api/ai/docs`.

## Seed Data

Seed JSON is generated from the frontend mock data with:

```bash
python scripts/convert_mock_js_to_json.py
```

The migration container runs `alembic upgrade head && python /app/scripts/seed_data.py`.
Embedding seeding is separate because it may spend API credits:

```bash
python scripts/seed_embeddings.py
```
