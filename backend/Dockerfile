FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2 and building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application (including the trained model artifact) and data
COPY backend /app/backend
COPY data /app/data
COPY database /app/database
COPY alembic.ini /app/alembic.ini

ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=120s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Bootstrap creates the schema, seeds an empty database, and trains the model if absent.
CMD ["sh", "-c", "python -m backend.app.bootstrap && exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
