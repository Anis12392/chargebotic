"""Shared FastAPI dependencies: auth, rate limiting, singletons."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from .config import settings
from .services.gis import GISEngine
from .services.inference import InferenceEngine
from .services.perch import PerchScorer
from .services.pipeline import AnalysisPipeline
from .services.vision import VisionAnalyzer

_pipeline: AnalysisPipeline | None = None


def get_pipeline() -> AnalysisPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = AnalysisPipeline(
            vision=VisionAnalyzer(),
            gis=GISEngine(),
            inference=InferenceEngine(),
            perch=PerchScorer(),
        )
    return _pipeline


def set_pipeline(pipeline: AnalysisPipeline | None) -> None:
    """Test hook for injecting a stubbed pipeline."""
    global _pipeline
    _pipeline = pipeline


async def require_admin(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> None:
    """Gate the admin surface.

    If no key is configured the admin API is refused outright in production and
    left open in development — an unset secret must never mean "no auth" on a
    deployed system.
    """
    if not settings.admin_api_key:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Admin API is disabled: ADMIN_API_KEY is not configured.",
            )
        return
    if not x_admin_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Admin-Key header"
        )
    # Constant-time comparison so the key cannot be recovered by timing.
    import hmac

    if not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin key")


class SlidingWindowLimiter:
    """In-process limiter.

    Adequate for a single replica. Behind more than one replica this becomes
    per-replica; swap in Redis before scaling out.
    """

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True


_analyze_limiter = SlidingWindowLimiter(settings.rate_limit_analyze_per_minute)


async def rate_limit_analyze(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client = forwarded.split(",")[0].strip()
    if not _analyze_limiter.check(client):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Rate limit exceeded ({settings.rate_limit_analyze_per_minute} analyses "
                "per minute). Slow down or contact us for a higher quota."
            ),
        )


PipelineDep = Annotated[AnalysisPipeline, Depends(get_pipeline)]
AdminDep = Annotated[None, Depends(require_admin)]
