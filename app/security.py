"""Security: rate limiter + optional API key auth."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

ROUTER_API_KEY = os.environ.get("ROUTER_API_KEY", "")

# ── Rate limiter (sliding window, in-memory) ──

RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "30"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW_SECS", "60"))  # 30 req / 60s


class SlidingWindowLimiter:
    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window_secs: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window_secs = window_secs
        self._clients: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_secs
        timestamps = self._clients[key]
        # prune old entries
        while timestamps and timestamps[0] < window_start:
            timestamps.pop(0)
        if len(timestamps) >= self.max_requests:
            return False
        timestamps.append(now)
        return True


_limiter = SlidingWindowLimiter()

RATE_LIMITED_PATHS = {"/v1/route"}


async def rate_limit_middleware(request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
    if request.method == "POST" and request.url.path in RATE_LIMITED_PATHS:
        client_ip = request.client.host if request.client else "unknown"
        if not _limiter.check(client_ip):
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit_exceeded", "message": f"Max {RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW}s. Try again later."},
            )
    return await call_next(request)


# ── Optional API key auth ──

AUTH_EXEMPT_PATHS = {"/", "/playground", "/v1/health", "/v1/metrics", "/v1/metrics/prometheus", "/v1/recent", "/v1/models"}


async def auth_middleware(request: Request, call_next: Callable[[Request], Awaitable[Any]]) -> Any:
    if not ROUTER_API_KEY:
        return await call_next(request)
    if request.url.path in AUTH_EXEMPT_PATHS:
        return await call_next(request)
    auth = request.headers.get("Authorization", "")
    if auth == f"Bearer {ROUTER_API_KEY}":
        return await call_next(request)
    return JSONResponse(status_code=401, content={"error": "unauthorized", "message": "Send Authorization: Bearer <ROUTER_API_KEY>"})


def setup_security(app: FastAPI) -> None:
    if ROUTER_API_KEY:
        app.middleware("http")(auth_middleware)
        print(f"  🔐 Auth: enabled (via ROUTER_API_KEY)")
    else:
        print(f"  🔓 Auth: disabled (set ROUTER_API_KEY to enable)")
    app.middleware("http")(rate_limit_middleware)
    print(f"  ⏱  Rate limit: {RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW}s on POST /v1/route")
