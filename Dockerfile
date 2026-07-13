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

# PRD_Report_Master_Redesign: 보고서 HTML→PDF 렌더용 Chromium 설치
# --with-deps 가 필요한 OS 라이브러리(libnss3, libatk 등)까지 apt로 설치한다.
RUN playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/data/thumbnails /app/logs

# Expose port
EXPOSE 8000

# PRD v4.10 Phase 2 (2026-06-25): HTTPS 도입 (mkcert)
# certs/server.crt + certs/server.key 가 ./certs 호스트 디렉터리에서 마운트되면 HTTPS 활성화
#
# v6.0-cert_installer_fix (2026-07-06, 버그 6):
#   기존엔 인증서 미존재 시 조용히 HTTP fallback → healthcheck(HTTPS 강제)와 충돌 발생하고,
#   클라(.NET, HTTPS 강제)가 SSL 오류 후 503 표시. 원인 파악이 어려웠음.
#   개선: 인증서 없으면 명확한 에러 로그 후 exit 1 (fail-fast).
#         개발 편의로 HTTP가 필요하면 ALLOW_HTTP_FALLBACK=true env를 명시적으로 지정.
CMD ["sh", "-c", "if [ -f /app/certs/server.crt ] && [ -f /app/certs/server.key ]; then echo '[HTTPS] certs OK - uvicorn HTTPS 기동'; exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile /app/certs/server.key --ssl-certfile /app/certs/server.crt; elif [ \"${ALLOW_HTTP_FALLBACK:-false}\" = 'true' ]; then echo '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'; echo '[WARN] ALLOW_HTTP_FALLBACK=true - HTTP 평문 기동'; echo '[WARN] 프로덕션에서는 반드시 인증서 배치 후 이 env 제거'; echo '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'; exec uvicorn app.main:app --host 0.0.0.0 --port 8000; else echo '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'; echo '[FATAL] /app/certs/server.crt server.key 미존재 - 서버 기동 중단'; echo '[FATAL] 조치:'; echo '[FATAL]   1) certs/server_install.exe 실행 (mkcert 자동 발급)'; echo '[FATAL]   2) 또는 mkcert -install && mkcert -cert-file certs/server.crt -key-file certs/server.key localhost 127.0.0.1'; echo '[FATAL]   3) 개발 편의 HTTP 허용: ALLOW_HTTP_FALLBACK=true (프로덕션 금지)'; echo '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'; exit 1; fi"]