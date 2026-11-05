import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

# In-memory limiter suitable for single-process academic demos.
# Replace with Redis-backed limiter for multi-replica deployments.
_buckets: dict[str, deque[float]] = defaultdict(deque)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    AUTH_PREFIXES = (
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/change-password",
    )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if request.method.upper() == "POST" and any(path.startswith(p) for p in self.AUTH_PREFIXES):
            settings = get_settings()
            client = request.client.host if request.client else "unknown"
            key = f"{client}:{path}"
            now = time.time()
            window = 60.0
            bucket = _buckets[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= settings.auth_rate_limit_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many authentication attempts. Try again shortly.",
                )
            bucket.append(now)
        return await call_next(request)
