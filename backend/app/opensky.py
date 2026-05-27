from __future__ import annotations

from typing import Any

import httpx

from app.config import OPENSKY_STATES_URL
from backend.app.repository import upsert_entity_and_position


async def fetch_states(client: httpx.AsyncClient) -> tuple[int | None, list[list[Any]]]:
    r = await client.get(OPENSKY_STATES_URL, timeout=30.0)
    r.raise_for_status()
    data = r.json()
    return data.get("time"), data.get("states") or []


def state_to_feature(row: list[Any]) -> dict[str, Any] | None:
    """
    OpenSky state vector indices (see OpenSky REST docs).
    Skip rows without lat/lon.
    """
    if not row or len(row) < 11:
        return None
    icao24 = (row[0] or "").strip().lower()
    if not icao24:
        return None
    lon, lat = row[5], row[6]
    if lon is None or lat is None:
        return None
    callsign = (row[1] or "").strip() or None
    origin_country = row[2] or None
    baro_altitude = row[7]
    on_ground = bool(row[8]) if row[8] is not None else False
    velocity = row[9]
    true_track = row[10]
    vertical_rate = row[11] if len(row) > 11 else None

    feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
        "properties": {
            "icao24": icao24,
            "callsign": callsign,
            "origin_country": origin_country,
            "baro_altitude_m": baro_altitude,
            "on_ground": on_ground,
            "velocity_m_s": velocity,
            "true_track_deg": true_track,
            "vertical_rate_m_s": vertical_rate,
        },
    }
    return feature


def state_to_model_fields(row: list[Any]) -> dict[str, Any] | None:
    f = state_to_feature(row)
    if not f:
        return None
    p = f["properties"]
    lon, lat = f["geometry"]["coordinates"]
    return {
        "icao24": p["icao24"],
        "callsign": p["callsign"],
        "origin_country": p["origin_country"],
        "lon": lon,
        "lat": lat,
        "baro_altitude_m": p["baro_altitude_m"],
        "on_ground": p["on_ground"],
        "velocity_m_s": p["velocity_m_s"],
        "true_track_deg": p["true_track_deg"],
        "vertical_rate_m_s": p["vertical_rate_m_s"],
    }

async def process_states(session, states, ts) -> list[dict]:
    features: list[dict] = []

    for row in states:
        fields = state_to_model_fields(row)
        if not fields:
            continue

        feat = await upsert_entity_and_position(
            session,
            icao24=fields["icao24"],
            callsign=fields["callsign"],
            origin_country=fields["origin_country"],
            lon=fields["lon"],
            lat=fields["lat"],
            baro_altitude_m=fields["baro_altitude_m"],
            velocity_m_s=fields["velocity_m_s"],
            true_track_deg=fields["true_track_deg"],
            vertical_rate_m_s=fields["vertical_rate_m_s"],
            on_ground=fields["on_ground"],
            ts=ts,
        )

        if feat:
            features.append(feat)

    return features
