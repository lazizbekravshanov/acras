FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV, WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (for layer caching)
COPY backend/pyproject.toml .

# Install CPU-only PyTorch first (avoids pulling ~5GB CUDA libraries)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -e .

# Copy backend code
COPY backend/ .

# Railway sets PORT env var
ENV PORT=8000
EXPOSE 8000

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
