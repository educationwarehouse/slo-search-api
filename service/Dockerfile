FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user
RUN useradd -m -u 1000 slo && mkdir -p /app && chown -R slo:slo /app

WORKDIR /app

# Install dependencies with uv (no cache)
COPY requirements-dev.txt .
RUN uv pip install --system --no-cache -r requirements-dev.txt

# Code comes from volume mount, not COPY
USER slo

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/stats')"

# Run application
CMD ["uvicorn", "api_fastapi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
