# Build a minimal Python image with Firefox and geckodriver for Selenium
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV DEBIAN_FRONTEND=noninteractive

# Install Firefox ESR, geckodriver and minimal runtime dependencies
RUN apt-get update \
     && apt-get install -y --no-install-recommends \
         ca-certificates curl wget \
         firefox-esr \
         libasound2 \
     && apt-get update && apt-get install -y ca-certificates \
     && update-ca-certificates \
     && rm -rf /var/lib/apt/lists/*

# Optional: verify firefox install
RUN firefox --version || true

WORKDIR /app

# Copy only requirements first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source
COPY . .

# Ensure Python can find the src/ layout
ENV PYTHONPATH=/app/src

# Note: DB connection settings should be provided at runtime (e.g., via docker-compose)

# Default command runs the scraper from src; docker-compose can override to run the API server.
CMD ["python", "-m", "app", "--config", "./config/config.json"]
