# GOP API Server Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    fonts-nanum \
    fontconfig \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/data/thumbnails /app/logs

# Expose port
EXPOSE 8000

# PRD v4.10 Phase 2 (2026-06-25): HTTPS 도입 (mkcert)
# certs/server.crt + certs/server.key 가 ./certs 호스트 디렉터리에서 마운트되면 HTTPS 활성화
# 인증서 미존재 시 평문 HTTP fallback (개발 환경 호환)
CMD ["sh", "-c", "if [ -f /app/certs/server.crt ] && [ -f /app/certs/server.key ]; then exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile /app/certs/server.key --ssl-certfile /app/certs/server.crt; else exec uvicorn app.main:app --host 0.0.0.0 --port 8000; fi"]