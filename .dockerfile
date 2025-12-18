# ============================================================================
# FILE: Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port (if adding FastAPI later)
EXPOSE 8000

# Run application
CMD ["python", "-m", "src.main"]
