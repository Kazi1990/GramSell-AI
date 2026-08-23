import secrets
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings
from .auth import verify_token

class RequestSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or secrets.token_hex(16)
        request.state.request_id = request_id
        public_path = request.url.path in {"/health", "/ready", "/docs", "/openapi.json", "/redoc"} or request.url.path.startswith("/api/auth/")
        if request.url.path.startswith("/api/") and not public_path:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_request_body_bytes:
                response = JSONResponse(status_code=413, content={"detail": "Request body too large"})
                response.headers["x-request-id"] = request_id
                return response
            if settings.write_api_key_required:
                supplied = request.headers.get("x-gramsell-api-key")
                bearer = request.headers.get("authorization", "")
                token_payload = verify_token(bearer[7:].strip()) if bearer.lower().startswith("bearer ") else None
                api_ok = bool(settings.internal_api_key and secrets.compare_digest(supplied or "", settings.internal_api_key))
                if not api_ok and not token_payload:
                    response = JSONResponse(status_code=401, content={"detail": "Authentication required"})
                    response.headers["x-request-id"] = request_id
                    return response
                request.state.seller_id = token_payload.get("seller_id") if token_payload else None
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
