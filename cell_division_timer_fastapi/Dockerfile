# Cell Division Timer API - Production Container Image
FROM python:3.12-slim

WORKDIR /app

# System dependencies required to build psycopg2-binary / other wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY scripts ./scripts

# Runtime data/output directories (mounted as volumes in docker-compose)
RUN mkdir -p /app/data /app/output

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run Alembic migrations, then start the API server.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
