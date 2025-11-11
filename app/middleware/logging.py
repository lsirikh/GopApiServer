"""
API Logging Middleware
Logs all API requests to database with Client UUID and Request ID tracking
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.models.log import ApiLog
from app.database import SessionLocal
import time


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

        # Call next middleware/endpoint
        response = await call_next(request)

        # Generate description
        description = self.get_description(request.method, path, response.status_code)

        # Log to database
        try:
            db: Session = SessionLocal()
            log_entry = ApiLog(
                resource=resource,
                method=request.method,
                client_uuid=client_uuid,
                request_id=request_id,
                description=description,
                status_code=response.status_code
            )
            db.add(log_entry)
            db.commit()
            db.close()
        except Exception as e:
            # Don't let logging errors break the request
            print(f"Logging error: {e}")

        return response
