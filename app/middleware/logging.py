"""
API Logging Middleware
Logs all API requests to database with Client UUID and Request ID tracking
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.models.log import ApiLog
from app.database import SessionLocal
import time
import json


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

        # Log to database
        db: Session = SessionLocal()
        try:
            log_entry = ApiLog(
                resource=resource,
                method=request.method,
                client_uuid=client_uuid,
                request_id=request_id,
                description=description,
                status_code=response.status_code,
                body=body,
                param=query_params,
                error_message=error_message
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            # Don't let logging errors break the request
            print(f"Logging error: {e}")
        finally:
            db.close()

        return response
