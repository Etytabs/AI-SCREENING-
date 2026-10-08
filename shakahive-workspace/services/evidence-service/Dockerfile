FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module
COPY shared /app/shared

# Copy service code
COPY services/evidence-service /app

# Expose port
EXPOSE 8011

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011", "--workers", "2"]
