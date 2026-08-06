from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Entity, Position


async def upsert_entity_and_position(
    session: AsyncSession,
    *,
    icao24: str,
    callsign: str | None,
    origin_country: str | None,
    lon: float,
    lat: float,
    baro_altitude_m: float | None,
    velocity_m_s: float | None,
    true_track_deg: float | None,
    vertical_rate_m_s: float | None,
    on_ground: bool,
    ts: datetime,
) -> dict[str, Any] | None:
    await session.execute(
        insert(Entity)
        .values(
            icao24=icao24,
            callsign=callsign,
            origin_country=origin_country,
            last_seen=ts,
        )
        .on_conflict_do_update(
            index_elements=[Entity.icao24],
            set_={
                "callsign": callsign,
                "origin_country": origin_country,
                "last_seen": ts,
            },
        )
    )

    geom = WKTElement(f"POINT({lon} {lat})", srid=4326)
    pos = Position(
        icao24=icao24,
        t=ts,
        geom=geom,
        baro_altitude_m=baro_altitude_m,
        velocity_m_s=velocity_m_s,
        true_track_deg=true_track_deg,
        vertical_rate_m_s=vertical_rate_m_s,
        on_ground=on_ground,
    )
    session.add(pos)

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "icao24": icao24,
            "callsign": callsign,
            "origin_country": origin_country,
            "baro_altitude_m": baro_altitude_m,
            "on_ground": on_ground,
            "velocity_m_s": velocity_m_s,
            "true_track_deg": true_track_deg,
            "vertical_rate_m_s": vertical_rate_m_s,
            "time": ts.isoformat(),
        },
    }


async def fetch_viewport_geojson(
    session: AsyncSession,
    *,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    max_age_hours: int = 2,
    limit: int = 8000,
) -> dict[str, Any]:
    """Latest position per ICAO24 inside bbox (PostgreSQL DISTINCT ON)."""
    cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
    q = text("""
        SELECT DISTINCT ON (p.icao24)
            p.icao24,
            ST_AsGeoJSON(p.geom)::json AS geom,
            p.baro_altitude_m,
            p.velocity_m_s,
            p.true_track_deg,
            p.vertical_rate_m_s,
            p.on_ground,
            p.t,
            e.callsign,
            e.origin_country
        FROM positions p
        JOIN entities e ON e.icao24 = p.icao24
        WHERE p.t > :cutoff
          AND ST_Intersects(
            p.geom,
            ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326)
          )
        ORDER BY p.icao24, p.t DESC
        LIMIT :limit
        """)
    result = await session.execute(
        q,
        {
            "cutoff": cutoff,
            "min_lon": min_lon,
            "min_lat": min_lat,
            "max_lon": max_lon,
            "max_lat": max_lat,
            "limit": limit,
        },
    )
    rows = result.mappings().all()
    features: list[dict[str, Any]] = []
    for row in rows:
        features.append(
            {
                "type": "Feature",
                "geometry": row["geom"],
                "properties": {
                    "icao24": row["icao24"],
                    "callsign": row["callsign"],
                    "origin_country": row["origin_country"],
                    "baro_altitude_m": row["baro_altitude_m"],
                    "velocity_m_s": row["velocity_m_s"],
                    "true_track_deg": row["true_track_deg"],
                    "vertical_rate_m_s": row["vertical_rate_m_s"],
                    "on_ground": row["on_ground"],
                    "time": row["t"].isoformat() if row["t"] else None,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


async def prune_old_positions(session: AsyncSession, retention_hours: int) -> None:
    cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)
    await session.execute(delete(Position).where(Position.t < cutoff))
