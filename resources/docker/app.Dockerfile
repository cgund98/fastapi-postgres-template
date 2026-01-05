FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-root

# Copy application code
COPY . .

# Expose port (for API server)
EXPOSE 8000

# Default command runs API server
# Override CMD in docker-compose or deployment to run worker:
# CMD ["python", "-m", "entry.worker.main"]
CMD ["uvicorn", "entry.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

