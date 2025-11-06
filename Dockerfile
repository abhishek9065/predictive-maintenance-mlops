# Multi-stage build for training container
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed models/katib mlruns

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MLFLOW_TRACKING_URI=file:///app/mlruns

# Default command (can be overridden by Katib)
CMD ["python", "katib_tuning.py", "--model=random_forest"]
