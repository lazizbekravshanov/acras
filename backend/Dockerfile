FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (libpq for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies (layer caching)
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy backend code
COPY backend/ .

# Railway sets PORT env var
ENV PORT=8000
EXPOSE 8000

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
