FROM python:3.11-slim

WORKDIR /app

# Optional but helpful for sqlite + certs
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md main.py /app/
COPY merchantbot /app/merchantbot

RUN pip install --no-cache-dir .

# Keep DB in a mounted folder
ENV DATABASE_PATH=/data/merchantbot.db
ENV WEBHOOK_BIND_HOST=0.0.0.0

CMD ["python", "main.py"]