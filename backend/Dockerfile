# syntax=docker/dockerfile:1.4
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Use a persistent build cache for pip downloads to avoid re-downloading
# large wheels on subsequent builds. Requires BuildKit (`DOCKER_BUILDKIT=1`).
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /app/faiss_indexes

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
