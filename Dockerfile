FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 slo && mkdir -p /app && chown -R slo:slo /app

WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY --chown=slo:slo *.py ./
COPY --chown=slo:slo config.py ./

# Switch to non-root user
USER slo

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/stats')"

# Run application
CMD ["uvicorn", "api_fastapi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
