FROM python:3.11-slim

WORKDIR /app

# System deps for pymupdf (PDF parsing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared lib and service code
COPY ../../shared /app/shared
COPY . /app

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
