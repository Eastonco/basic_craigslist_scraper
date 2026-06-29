# One image for both the web app and the scraper loop. No browser inside — the
# scraper talks to the standalone Selenium service (see docker-compose.yml).
FROM python:3.11-slim

WORKDIR /app

# Stream print()/logs straight to docker logs instead of block-buffering them
# (Python fully buffers stdout when it's not a TTY, e.g. under Docker).
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command is overridden per-service in docker-compose.yml.
CMD ["python", "main.py"]
