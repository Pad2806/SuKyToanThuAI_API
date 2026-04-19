FROM python:3.14-rc-slim

WORKDIR /app

# Install system dependencies if required (like libpq for psycopg2, fonts for reportlab)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Docker compose will override this command and port
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
