"""The GIS cache must never issue concurrent operations on one AsyncSession.

Regression cover for a bug found by running the app: ``collect`` fans out to
three sources with ``asyncio.gather``, all sharing the request's session.
AsyncSession forbids concurrent operations, so every cache read raised — and
because cache errors are deliberately swallowed so they can never fail a
request, it showed up only as a log line while the cache silently never worked
and every request went to Overpass.
"""

from __future__ import annotations

import asyncio

import pytest

from app.services.gis import CacheHandle, GISEngine


class ConcurrencyTrackingSession:
    """Fails loudly if two operations overlap, the way AsyncSession does."""

    def __init__(self, delay: float = 0.01) -> None:
        self.in_flight = 0
        self.max_in_flight = 0
        self.executions = 0
        self._delay = delay

    async def _operation(self):
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        if self.in_flight > 1:
            self.in_flight -= 1
            raise RuntimeError(
                "This session is provisioning a new connection; "
                "concurrent operations are not permitted"
            )
        await asyncio.sleep(self._delay)
        self.in_flight -= 1

    async def execute(self, *_args, **_kwargs):
        self.executions += 1
        await self._operation()
        return _EmptyResult()

    async def flush(self) -> None:
        await self._operation()

    def add(self, _obj) -> None:
        return None


class _EmptyResult:
    def scalar_one_or_none(self):
        return None


class TestCacheHandleSerialisation:
    async def test_concurrent_reads_do_not_overlap(self):
        session = ConcurrencyTrackingSession()
        cache = CacheHandle(session)

        await asyncio.gather(*(cache.read(f"key-{i}") for i in range(6)))

        assert session.executions == 6, "every read must reach the session"
        assert session.max_in_flight == 1, "reads must be serialised"

    async def test_concurrent_reads_and_writes_do_not_overlap(self):
        session = ConcurrencyTrackingSession()
        cache = CacheHandle(session)

        await asyncio.gather(
            cache.read("a"),
            cache.write("b", "overpass", 37.0, -122.0, 400, {"elements": []}),
            cache.read("c"),
            cache.write("d", "hifld", 37.0, -122.0, 400, {"features": []}),
        )

        assert session.max_in_flight == 1

    async def test_a_missing_session_is_a_no_op(self):
        cache = CacheHandle(None)
        assert await cache.read("anything") is None
        await cache.write("k", "overpass", 0.0, 0.0, 100, {})


class TestCollectFanOut:
    async def test_collect_never_overlaps_session_operations(self, monkeypatch):
        """The end-to-end shape: three sources, one session, no overlap."""
        from app.config import settings

        monkeypatch.setattr(settings, "external_gis_enabled", True)

        session = ConcurrencyTrackingSession()
        engine = GISEngine()

        # Every network call fails, which is the path that still exercises the
        # cache read on all three sources.
        async def boom(*_args, **_kwargs):
            raise RuntimeError("network disabled in tests")

        monkeypatch.setattr(engine, "_post", boom)
        monkeypatch.setattr(engine, "_get", boom)

        context = await engine.collect(session, 37.7749, -122.4194, 400)

        assert session.max_in_flight == 1, "cache access must be serialised across sources"
        assert session.executions == 3, "each source checks the cache exactly once"
        # Failures are disclosed rather than swallowed into a clean-looking result.
        assert len(context.errors) == 3
        assert context.assets == []

    async def test_disabled_gis_makes_no_session_calls(self, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "external_gis_enabled", False)
        session = ConcurrencyTrackingSession()

        context = await GISEngine().collect(session, 37.7749, -122.4194, 400)

        assert session.executions == 0
        assert context.errors == ["External GIS lookups are disabled by configuration"]


@pytest.mark.parametrize("radius", [100, 400, 5000])
async def test_cache_key_is_stable_for_a_location(radius):
    from app.services.gis import _cache_key

    first = _cache_key("overpass", 37.7749, -122.4194, radius)
    second = _cache_key("overpass", 37.7749, -122.4194, radius)
    assert first == second

    # ~11 m grid: a pole-by-pole walk down one street reuses the same entry.
    nearby = _cache_key("overpass", 37.77492, -122.41942, radius)
    assert nearby == first

    far = _cache_key("overpass", 37.8000, -122.4194, radius)
    assert far != first
