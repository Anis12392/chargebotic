"""GIS engine: find the power infrastructure around a capture point.

Sources, in descending order of trust:
  1. OpenStreetMap via Overpass — hand-surveyed ``power=*`` tags. These carry
     ``voltage``, ``operator``, ``circuits``, ``ref`` (pole/circuit ID) and are
     the single most valuable signal the system has.
  2. HIFLD / USGS ArcGIS feature services — authoritative transmission line and
     substation geometry for the United States, but no distribution coverage.
  3. Locally loaded utility territory polygons (state GIS portals), if the
     operator has imported any.

Every external call is cached in Postgres keyed on a rounded location so a
field crew photographing twenty poles on one street hits Overpass once.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import GISCacheEntry
from ..schemas import GISAsset, GISContext

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_008.8

OVERPASS_QUERY = """\
[out:json][timeout:{timeout}];
(
  node(around:{radius},{lat},{lon})["power"];
  way(around:{radius},{lat},{lon})["power"];
  relation(around:{radius},{lat},{lon})["power"];
  node(around:{radius},{lat},{lon})["utility"="power"];
  way(around:{radius},{lat},{lon})["man_made"="utility_pole"];
);
out tags center {maxsize};
"""

#: OSM ``power=*`` values we care about, mapped to our internal asset kinds.
POWER_TAG_TO_KIND: dict[str, str] = {
    "line": "line",
    "minor_line": "minor_line",
    "cable": "cable",
    "tower": "tower",
    "pole": "pole",
    "portal": "portal",
    "substation": "substation",
    "transformer": "transformer",
    "switch": "switch",
    "plant": "plant",
    "generator": "generator",
    "insulator": "insulator",
    "terminal": "terminal",
    "catenary_mast": "catenary_mast",
    "connection": "connection",
}


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial compass bearing from point 1 to point 2."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dlambda)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def parse_voltages(raw: str | None) -> list[int]:
    """OSM voltage tags look like ``115000`` or ``12470;4160`` or ``69 kV``."""
    if not raw:
        return []
    values: list[int] = []
    for chunk in re.split(r"[;,/]", str(raw)):
        chunk = chunk.strip().lower()
        if not chunk:
            continue
        match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(kv|v)?$", chunk)
        if not match:
            continue
        number = float(match.group(1))
        unit = match.group(2)
        if unit == "kv":
            number *= 1000
        elif unit is None and number < 1500:
            # Bare numbers under 1500 in OSM power tags are almost always kV
            # written without the unit (e.g. voltage=115). Volt values that low
            # would be a service drop, which is not tagged as a power line.
            number *= 1000
        values.append(int(round(number)))
    return sorted(set(values), reverse=True)


class CacheHandle:
    """Serialised access to the request's session for cache reads and writes.

    ``collect`` fans out to three GIS sources with ``asyncio.gather``, and they
    all share one ``AsyncSession``. AsyncSession does not permit concurrent
    operations — overlapping calls raise "this session is provisioning a new
    connection". Because cache errors are deliberately swallowed so they can
    never fail a request, that surfaced only as a log line while the cache
    silently never worked, sending every request to Overpass.

    The lock is per-collect, not per-engine, so concurrent requests still run
    independently.
    """

    def __init__(self, session: AsyncSession | None) -> None:
        self.session = session
        self._lock = asyncio.Lock()

    async def read(self, key: str) -> dict[str, Any] | None:
        if self.session is None:
            return None
        async with self._lock:
            try:
                result = await self.session.execute(
                    select(GISCacheEntry).where(GISCacheEntry.cache_key == key)
                )
                entry = result.scalar_one_or_none()
            except Exception as exc:  # pragma: no cover - cache must never break a request
                logger.warning("GIS cache read failed: %s", exc)
                return None
        if entry is None or entry.expires_at <= datetime.now(UTC):
            return None
        return entry.payload

    async def write(
        self,
        key: str,
        source: str,
        lat: float,
        lon: float,
        radius: int,
        payload: dict[str, Any],
    ) -> None:
        if self.session is None:
            return
        async with self._lock:
            try:
                existing = await self.session.execute(
                    select(GISCacheEntry).where(GISCacheEntry.cache_key == key)
                )
                entry = existing.scalar_one_or_none()
                expires = datetime.now(UTC) + timedelta(
                    seconds=settings.gis_cache_ttl_seconds
                )
                if entry is None:
                    self.session.add(
                        GISCacheEntry(
                            cache_key=key,
                            source=source,
                            latitude=lat,
                            longitude=lon,
                            radius_m=radius,
                            payload=payload,
                            expires_at=expires,
                        )
                    )
                else:
                    entry.payload = payload
                    entry.expires_at = expires
                await self.session.flush()
            except Exception as exc:  # pragma: no cover
                logger.warning("GIS cache write failed: %s", exc)


def _cache_key(source: str, lat: float, lon: float, radius: int) -> str:
    # ~11 m grid at 4 decimal places; enough to dedupe a pole-by-pole walk.
    payload = f"{source}:{lat:.4f}:{lon:.4f}:{radius}"
    return hashlib.sha256(payload.encode()).hexdigest()[:40]


class GISEngine:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def collect(
        self,
        session: AsyncSession | None,
        latitude: float,
        longitude: float,
        radius_m: int | None = None,
    ) -> GISContext:
        radius = min(radius_m or settings.gis_default_radius_m, settings.gis_max_radius_m)
        context = GISContext(
            query_latitude=latitude, query_longitude=longitude, radius_m=radius
        )

        if not settings.external_gis_enabled:
            context.errors.append("External GIS lookups are disabled by configuration")
            return context

        cache = CacheHandle(session)
        results = await asyncio.gather(
            self._overpass(cache, latitude, longitude, radius),
            self._arcgis(
                cache,
                settings.usgs_hifld_transmission_url,
                "hifld_transmission",
                latitude,
                longitude,
                max(radius, 2_000),
                "line",
            ),
            self._arcgis(
                cache,
                settings.usgs_hifld_substation_url,
                "hifld_substation",
                latitude,
                longitude,
                max(radius, 5_000),
                "substation",
            ),
            return_exceptions=True,
        )

        source_names = ["overpass", "hifld_transmission", "hifld_substation"]
        for name, result in zip(source_names, results, strict=True):
            if isinstance(result, BaseException):
                logger.warning("GIS source %s failed: %s", name, result)
                context.errors.append(f"{name}: {type(result).__name__}")
                continue
            assets, cached = result
            context.sources_queried.append(name)
            context.assets.extend(assets)
            context.cached = context.cached or cached

        self._finalise(context)
        return context

    # -- Overpass ----------------------------------------------------------

    async def _overpass(
        self,
        cache: CacheHandle,
        lat: float,
        lon: float,
        radius: int,
    ) -> tuple[list[GISAsset], bool]:
        key = _cache_key("overpass", lat, lon, radius)
        cached_payload = await cache.read(key)
        if cached_payload is not None:
            return self._parse_overpass(cached_payload, lat, lon), True

        query = OVERPASS_QUERY.format(
            timeout=int(settings.overpass_timeout_seconds),
            radius=radius,
            lat=lat,
            lon=lon,
            maxsize="",
        )
        payload = await self._post(
            settings.overpass_url,
            data={"data": query},
            headers={"User-Agent": settings.overpass_user_agent},
        )
        await cache.write(key, "overpass", lat, lon, radius, payload)
        return self._parse_overpass(payload, lat, lon), False

    def _parse_overpass(self, payload: dict[str, Any], lat: float, lon: float) -> list[GISAsset]:
        assets: list[GISAsset] = []
        for element in payload.get("elements", []) or []:
            tags = element.get("tags") or {}
            power = tags.get("power") or tags.get("man_made")
            kind = POWER_TAG_TO_KIND.get(power or "", None)
            if kind is None:
                if tags.get("man_made") == "utility_pole":
                    kind = "pole"
                else:
                    continue

            centre = element.get("center") or {}
            a_lat = element.get("lat", centre.get("lat"))
            a_lon = element.get("lon", centre.get("lon"))

            distance = None
            bearing = None
            if a_lat is not None and a_lon is not None:
                distance = round(haversine_m(lat, lon, a_lat, a_lon), 1)
                bearing = round(bearing_deg(lat, lon, a_lat, a_lon), 1)

            assets.append(
                GISAsset(
                    source="overpass",
                    element_type=element.get("type", "node"),
                    element_id=str(element.get("id")),
                    asset_kind=kind,
                    name=tags.get("name"),
                    operator=tags.get("operator") or tags.get("owner"),
                    voltage_v=parse_voltages(tags.get("voltage")),
                    circuits=_as_int(tags.get("circuits")),
                    cables=_as_int(tags.get("cables")),
                    wires=tags.get("wires"),
                    ref=tags.get("ref") or tags.get("ref:pole") or tags.get("line"),
                    frequency_hz=_as_float(tags.get("frequency")),
                    latitude=a_lat,
                    longitude=a_lon,
                    distance_m=distance,
                    bearing_deg=bearing,
                    tags=tags,
                )
            )
        return assets

    # -- ArcGIS feature services (HIFLD / USGS / state portals) -------------

    async def _arcgis(
        self,
        cache: CacheHandle,
        url: str | None,
        source_name: str,
        lat: float,
        lon: float,
        radius: int,
        kind: str,
    ) -> tuple[list[GISAsset], bool]:
        if not url:
            return [], False

        key = _cache_key(source_name, lat, lon, radius)
        cached_payload = await cache.read(key)
        if cached_payload is not None:
            return self._parse_arcgis(cached_payload, lat, lon, source_name, kind), True

        params = {
            "f": "json",
            "geometry": json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "outSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": str(radius),
            "units": "esriSRUnit_Meter",
            "outFields": "*",
            "returnGeometry": "true",
            "resultRecordCount": "50",
        }
        payload = await self._get(url, params=params)
        await cache.write(key, source_name, lat, lon, radius, payload)
        return self._parse_arcgis(payload, lat, lon, source_name, kind), False

    def _parse_arcgis(
        self,
        payload: dict[str, Any],
        lat: float,
        lon: float,
        source_name: str,
        kind: str,
    ) -> list[GISAsset]:
        assets: list[GISAsset] = []
        for feature in payload.get("features", []) or []:
            attrs = feature.get("attributes") or {}
            geometry = feature.get("geometry") or {}
            a_lat, a_lon = _arcgis_representative_point(geometry)

            distance = None
            bearing = None
            if a_lat is not None and a_lon is not None:
                distance = round(haversine_m(lat, lon, a_lat, a_lon), 1)
                bearing = round(bearing_deg(lat, lon, a_lat, a_lon), 1)

            voltages: list[int] = []
            for field in ("VOLTAGE", "VOLT_CLASS", "MAX_VOLT", "voltage"):
                raw = attrs.get(field)
                if raw in (None, "", "NOT AVAILABLE", -999999, "-999999"):
                    continue
                if isinstance(raw, int | float) and raw > 0:
                    # HIFLD publishes transmission voltage in kV.
                    voltages.append(int(round(float(raw) * 1000)))
                else:
                    voltages.extend(parse_voltages(str(raw)))
            voltages = sorted({v for v in voltages if v > 0}, reverse=True)

            operator = None
            for field in ("OWNER", "NAME", "OPERATOR", "HOLDING_CO"):
                value = attrs.get(field)
                if value and str(value).upper() not in {"NOT AVAILABLE", "UNKNOWN"}:
                    operator = str(value)
                    break

            assets.append(
                GISAsset(
                    source="hifld",
                    element_type="feature",
                    element_id=str(attrs.get("OBJECTID") or attrs.get("ID") or len(assets)),
                    asset_kind=kind,
                    name=str(attrs.get("NAME")) if attrs.get("NAME") else None,
                    operator=operator,
                    voltage_v=voltages,
                    latitude=a_lat,
                    longitude=a_lon,
                    distance_m=distance,
                    bearing_deg=bearing,
                    tags={k: v for k, v in attrs.items() if v not in (None, "")},
                    geometry=_arcgis_to_geojson(geometry),
                )
            )
        return assets

    # -- Post-processing ---------------------------------------------------

    def _finalise(self, context: GISContext) -> None:
        def sort_key(asset: GISAsset) -> float:
            return asset.distance_m if asset.distance_m is not None else float("inf")

        context.assets.sort(key=sort_key)

        line_kinds = {"line", "minor_line", "cable"}
        structure_kinds = {"tower", "pole", "portal"}

        context.nearest_line = next(
            (a for a in context.assets if a.asset_kind in line_kinds), None
        )
        context.nearest_structure = next(
            (a for a in context.assets if a.asset_kind in structure_kinds), None
        )
        context.nearest_substation = next(
            (a for a in context.assets if a.asset_kind == "substation"), None
        )

        operators: dict[str, int] = {}
        voltages: set[int] = set()
        for asset in context.assets:
            if asset.operator:
                operators[asset.operator] = operators.get(asset.operator, 0) + 1
            voltages.update(asset.voltage_v)

        context.operators = [
            name for name, _ in sorted(operators.items(), key=lambda kv: -kv[1])
        ]
        context.voltages_v = sorted(voltages, reverse=True)

    # -- HTTP + cache helpers ----------------------------------------------

    async def _post(self, url: str, **kwargs: Any) -> dict[str, Any]:
        client = self._client
        owns = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=settings.overpass_timeout_seconds)
        try:
            response = await client.post(url, **kwargs)
            response.raise_for_status()
            return response.json()
        finally:
            if owns:
                await client.aclose()

    async def _get(self, url: str, **kwargs: Any) -> dict[str, Any]:
        client = self._client
        owns = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=settings.overpass_timeout_seconds)
        try:
            response = await client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
        finally:
            if owns:
                await client.aclose()


def _arcgis_representative_point(geometry: dict[str, Any]) -> tuple[float | None, float | None]:
    if "y" in geometry and "x" in geometry:
        return geometry["y"], geometry["x"]
    paths = geometry.get("paths") or geometry.get("rings")
    if paths:
        first = paths[0]
        if first:
            mid = first[len(first) // 2]
            return mid[1], mid[0]
    return None, None


def _arcgis_to_geojson(geometry: dict[str, Any]) -> dict[str, Any] | None:
    if not geometry:
        return None
    if "x" in geometry and "y" in geometry:
        return {"type": "Point", "coordinates": [geometry["x"], geometry["y"]]}
    if geometry.get("paths"):
        return {"type": "MultiLineString", "coordinates": geometry["paths"]}
    if geometry.get("rings"):
        return {"type": "Polygon", "coordinates": geometry["rings"]}
    return None


def _as_int(value: Any) -> int | None:
    try:
        return int(str(value).split(";")[0])
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(str(value).split(";")[0])
    except (TypeError, ValueError):
        return None
