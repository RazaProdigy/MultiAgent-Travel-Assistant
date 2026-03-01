# MultiAgent Travel Assistant - Backend
FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (excludes __pycache__, .env, chroma_data via .dockerignore)
COPY . .

# ChromaDB data is persisted via volume; ensure directory exists
RUN mkdir -p /app/chroma_data

# Env vars are provided at runtime via docker-compose or host
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
