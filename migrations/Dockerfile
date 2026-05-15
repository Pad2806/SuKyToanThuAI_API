FROM python:3.12-slim

WORKDIR /app
COPY SuKyAI_API/migrations/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY SuKyAI_API/shared ./shared
RUN pip install --no-cache-dir --no-deps -e ./shared
COPY SuKyAI_API/migrations ./migrations
COPY SuKyAI_API/scripts ./scripts
COPY docs ./schema
WORKDIR /app/migrations
CMD ["sh", "-c", "alembic upgrade head && python /app/scripts/seed_data.py"]
