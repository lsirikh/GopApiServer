"""
Request ID Middleware
Generates or preserves X-Request-ID header for request tracking
"""
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Request-ID header
    - Auto-generates UUID if not provided
    - Preserves existing X-Request-ID if provided
    - Adds X-Request-ID to response headers
    """

    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            # Generate new UUID if not provided
            request_id = str(uuid.uuid4())

        # Store request_id in request state for access in endpoints
        request.state.request_id = request_id

        # Call the next middleware/endpoint
        response = await call_next(request)

        # Add X-Request-ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
