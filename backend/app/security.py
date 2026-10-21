"""Medidas de seguridad a nivel de aplicación: cabeceras, límite de solicitudes y de tamaño.

Limitaciones honestas:
  - El limitador es en memoria y por proceso. En producción con varias instancias debe
    complementarse con el límite del proxy/CDN o con Redis.
  - Aún no hay autenticación (FASE 6). Los endpoints de escritura están limitados pero abiertos.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_BODY_BYTES = 10_000


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Cross-Origin-Resource-Policy"] = "same-site"
        if request.url.path.startswith("/api"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
            response.headers["Cache-Control"] = "no-store"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int, write_per_minute: int, trust_proxy: bool = False) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self.write_per_minute = write_per_minute
        self.trust_proxy = trust_proxy
        self._hits: dict[tuple[str, str], deque] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        if self.trust_proxy:
            fwd = request.headers.get("x-forwarded-for")
            if fwd:
                return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        if not request.url.path.startswith("/api") or request.url.path == "/api/health":
            return await call_next(request)
        is_write = request.method in {"POST", "PUT", "PATCH", "DELETE"}
        limit = self.write_per_minute if is_write else self.per_minute
        bucket = (self._client_ip(request), "w" if is_write else "r")
        now = time.monotonic()
        q = self._hits[bucket]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            retry = int(60 - (now - q[0])) + 1
            return JSONResponse({"detail": "Demasiadas solicitudes. Intenta de nuevo en un momento."},
                                status_code=429, headers={"Retry-After": str(retry)})
        q.append(now)
        return await call_next(request)


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
            return JSONResponse({"detail": "Cuerpo de la solicitud demasiado grande."}, status_code=413)
        return await call_next(request)
