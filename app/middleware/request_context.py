import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Zet een request-id (voor de audit-trail) en basis security headers."""

    async def dispatch(self, request: Request, call_next):
        try:
            rid = str(uuid.UUID(request.headers.get("x-request-id", "")))
        except ValueError:
            rid = str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Content-Type-Options"] = "nosniff"
        if get_settings().cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
