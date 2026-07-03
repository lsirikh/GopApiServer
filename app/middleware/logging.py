"""
API Logging Middleware
Logs all API requests to database with Client UUID and Request ID tracking

v5.4 후속 — 문서 A-7 #1 대응:
- 이전: async dispatch 안에서 동기 SessionLocal() + INSERT + commit → 이벤트루프 블로킹.
  풀 30 커넥션이 idle-in-transaction으로 굳으면 /health까지 정지 (문서 A-2 ②③).
- 지금: 실 INSERT는 `asyncio.to_thread(...)`로 threadpool 이관 → 이벤트루프 자유.
  fire-and-forget 태스크로 발행하여 응답 지연도 최소화.
- 완전한 배치 큐+배치 INSERT는 v6.0 async 전환과 함께 도입 예정.
"""
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.models.log import ApiLog
from app.database import SessionLocal
import time
import json


def _persist_api_log_sync(
    *, resource, method, client_uuid, request_id,
    description, status_code, body, param, error_message,
) -> None:
    """threadpool에서 실행될 동기 INSERT — 이벤트루프 자유 유지."""
    db: Session = SessionLocal()
    try:
        log_entry = ApiLog(
            resource=resource,
            method=method,
            client_uuid=client_uuid,
            request_id=request_id,
            description=description,
            status_code=status_code,
            body=body,
            param=param,
            error_message=error_message,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        print(f"Logging error: {e}")
    finally:
        db.close()


class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests to database
    - Captures Request ID and Client UUID from headers
    - Records resource, method, description, and status code
    - Stores timestamp in ISO 8601 format
    """

    def get_description(self, method: str, path: str, status_code: int) -> str:
        """Generate description based on method and path"""
        resource_map = {
            "controllers": "제어기",
            "sensors": "센서",
            "cameras": "카메라",
            "detections": "탐지 이벤트",
            "malfunctions": "장애 이벤트",
            "connections": "연결 이벤트",
            "actions": "조치 이벤트",
        }

        action_map = {
            "GET": "조회",
            "POST": "생성",
            "PUT": "전체 수정",
            "PATCH": "부분 수정",
            "DELETE": "삭제",
        }

        # Extract resource from path
        parts = path.strip("/").split("/")
        resource_key = parts[-1] if len(parts) > 0 else "unknown"

        # Check if it's a detail endpoint (has ID)
        is_detail = len(parts) > 0 and parts[-1].isdigit()
        if is_detail and len(parts) >= 2:
            resource_key = parts[-2]

        resource_name = resource_map.get(resource_key, resource_key)
        action = action_map.get(method, method)

        # Generate description
        if status_code >= 400:
            return f"{resource_name} {action} 실패"
        elif is_detail:
            return f"{resource_name} {action}"
        else:
            if method == "GET":
                return f"{resource_name} 목록 {action}"
            return f"{resource_name} {action}"

    async def dispatch(self, request: Request, call_next):
        # Get headers
        client_uuid = request.headers.get("X-Client-UUID")
        request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

        # Get resource path (remove /api prefix)
        path = request.url.path
        resource = path.replace("/api/", "").strip("/")

        # Capture URL query parameters
        query_params = None
        if request.url.query:
            query_params = str(request.url.query)
            # Limit param length to prevent database overflow
            if len(query_params) > 1000:
                query_params = query_params[:997] + "..."

        # Capture request body for POST, PUT, PATCH methods
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = body_bytes.decode('utf-8')
                    # Limit body length to prevent database overflow
                    if len(body) > 2000:
                        body = body[:1997] + "..."
                # Re-create request with body (since body() consumes the stream)
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
            except Exception as e:
                print(f"Error capturing request body: {e}")

        # Call next middleware/endpoint
        response = await call_next(request)

        # Capture error message from response if status >= 400
        error_message = None
        if response.status_code >= 400:
            try:
                # For responses with body, try to extract error message
                if hasattr(response, 'body'):
                    body = response.body
                    if body:
                        response_data = json.loads(body.decode('utf-8'))
                        error_message = response_data.get('message') or response_data.get('detail')
                        # Limit error message length
                        if error_message and len(error_message) > 1000:
                            error_message = error_message[:997] + "..."
            except Exception as e:
                print(f"Error extracting error message: {e}")

        # Generate description
        description = self.get_description(request.method, path, response.status_code)

        # Skip logging for non-API routes (docs, openapi, static, health)
        # v5.4 P0-1: /reports/preview 제외 제거 — 인증 필요 엔드포인트는 감사 로그에 남긴다.
        if path in ("/docs", "/redoc", "/openapi.json", "/health", "/", "/favicon.ico"):
            return response

        # v5.4 후속 (A-7 #1): 이벤트루프 블로킹 해소 — sync INSERT를 threadpool로 이관.
        # fire-and-forget: 태스크 예약 후 즉시 return → 응답 지연 0, 실패해도 요청 흐름 무영향.
        try:
            asyncio.create_task(
                asyncio.to_thread(
                    _persist_api_log_sync,
                    resource=resource,
                    method=request.method,
                    client_uuid=client_uuid,
                    request_id=request_id,
                    description=description,
                    status_code=response.status_code,
                    body=body,
                    param=query_params,
                    error_message=error_message,
                )
            )
        except Exception as e:
            print(f"Log task schedule error: {e}")

        return response
