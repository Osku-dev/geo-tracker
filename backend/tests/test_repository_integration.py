from datetime import datetime, UTC, timedelta

import pytest
from sqlalchemy import select

from app.models import Entity, Position
from app.repository import fetch_aircraft_history, fetch_viewport_geojson, upsert_entity_and_position


@pytest.mark.asyncio
async def test_upsert_inserts_entity_and_position(db_session):
    ts = datetime(2025, 1, 1, tzinfo=UTC)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=ts,
    )

    await db_session.commit()

    entity_result = await db_session.execute(
        select(Entity).where(Entity.icao24 == "abc123")
    )
    entity = entity_result.scalar_one()

    position_result = await db_session.execute(
        select(Position).where(Position.icao24 == "abc123")
    )
    position = position_result.scalar_one()

    assert entity.callsign == "FIN123"
    assert entity.origin_country == "Finland"
    assert entity.last_seen == ts

    assert position.icao24 == "abc123"
    assert position.t == ts
    assert position.baro_altitude_m == 1000
    assert position.velocity_m_s == 250
    assert position.true_track_deg == 180
    assert position.vertical_rate_m_s == 5
    assert position.on_ground is False



@pytest.mark.asyncio
async def test_upsert_updates_existing_entity(db_session):
    first_ts = datetime(2025, 1, 1, tzinfo=UTC)
    second_ts = datetime(2025, 1, 1, 1, tzinfo=UTC)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=first_ts,
    )

    await db_session.commit()

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="NEW456",
        origin_country="Sweden",
        lon=25.00,
        lat=61.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=second_ts,
    )

    await db_session.commit()

    result = await db_session.execute(
        select(Entity).where(Entity.icao24 == "abc123")
    )
    entity = result.scalar_one()

    assert entity.callsign == "NEW456"
    assert entity.origin_country == "Sweden"
    assert entity.last_seen == second_ts

@pytest.mark.asyncio
async def test_upsert_stores_multiple_positions_for_same_entity(db_session):
    first_ts = datetime(2025, 1, 1, tzinfo=UTC)
    second_ts = datetime(2025, 1, 1, 1, tzinfo=UTC)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=first_ts,
    )

    await db_session.commit()

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=25.00,
        lat=61.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=second_ts,
    )

    await db_session.commit()

    result = await db_session.execute(
        select(Position)
        .where(Position.icao24 == "abc123")
        .order_by(Position.t)
    )
    positions = result.scalars().all()

    assert len(positions) == 2

    assert positions[0].t == first_ts
    assert positions[0].baro_altitude_m == 1000

    assert positions[1].t == second_ts
    assert positions[1].baro_altitude_m == 2000


@pytest.mark.asyncio
async def test_fetch_viewport_returns_latest_position_per_entity(db_session):
    now = datetime.now(UTC)
    first_ts = now - timedelta(hours=1)
    second_ts = now

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=first_ts,
    )

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=25.00,
        lat=61.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=second_ts,
    )

    await db_session.commit()

    result = await fetch_viewport_geojson(
        db_session,
        min_lon=20,
        min_lat=55,
        max_lon=30,
        max_lat=65,
    )

    assert len(result["features"]) == 1

    feature = result["features"][0]

    assert feature["properties"]["icao24"] == "abc123"
    assert feature["properties"]["baro_altitude_m"] == 2000
    assert feature["properties"]["velocity_m_s"] == 300
    assert feature["properties"]["true_track_deg"] == 90
    assert feature["properties"]["time"] == second_ts.isoformat()

    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [25.0, 61.0],
    }


@pytest.mark.asyncio
async def test_fetch_viewport_excludes_positions_outside_bbox(db_session):
    now = datetime.now(UTC)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=now,
    )

    await upsert_entity_and_position(
        db_session,
        icao24="xyz789",
        callsign="SAS456",
        origin_country="Sweden",
        lon=30.00,
        lat=70.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=now,
    )

    await db_session.commit()

    result = await fetch_viewport_geojson(
        db_session,
        min_lon=20,
        min_lat=55,
        max_lon=25,
        max_lat=65,
    )

    assert len(result["features"]) == 1

    feature = result["features"][0]

    assert feature["properties"]["icao24"] == "abc123"
    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [24.94, 60.17],
    }

@pytest.mark.asyncio
async def test_fetch_aircraft_history_returns_positions(db_session):
    now = datetime.now(UTC)
    first_ts = now - timedelta(hours=2)
    second_ts = now - timedelta(hours=1)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=first_ts,
    )

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=25.00,
        lat=61.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=second_ts,
    )

    await db_session.commit()

    result = await fetch_aircraft_history(
        db_session,
        icao24="abc123",
        hours=24,
    )

    assert len(result) == 2

    assert result[0]["icao24"] == "abc123"
    assert result[0]["t"] == first_ts
    assert result[0]["geom"]["coordinates"] == [24.94, 60.17]

    assert result[1]["icao24"] == "abc123"
    assert result[1]["t"] == second_ts
    assert result[1]["geom"]["coordinates"] == [25.0, 61.0]

@pytest.mark.asyncio
async def test_fetch_aircraft_history_only_returns_requested_aircraft(db_session):
    now = datetime.now(UTC)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=now,
    )

    await upsert_entity_and_position(
        db_session,
        icao24="xyz789",
        callsign="SAS456",
        origin_country="Sweden",
        lon=25.00,
        lat=61.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=now,
    )

    await db_session.commit()

    result = await fetch_aircraft_history(
        db_session,
        icao24="abc123",
        hours=24,
    )

    assert len(result) == 1
    assert result[0]["icao24"] == "abc123"

@pytest.mark.asyncio
async def test_fetch_aircraft_history_excludes_old_positions(db_session):
    now = datetime.now(UTC)

    recent_ts = now - timedelta(hours=23)
    old_ts = now - timedelta(hours=25)

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=24.94,
        lat=60.17,
        baro_altitude_m=1000,
        velocity_m_s=250,
        true_track_deg=180,
        vertical_rate_m_s=5,
        on_ground=False,
        ts=old_ts,
    )

    await upsert_entity_and_position(
        db_session,
        icao24="abc123",
        callsign="FIN123",
        origin_country="Finland",
        lon=25.00,
        lat=61.00,
        baro_altitude_m=2000,
        velocity_m_s=300,
        true_track_deg=90,
        vertical_rate_m_s=10,
        on_ground=False,
        ts=recent_ts,
    )

    await db_session.commit()

    result = await fetch_aircraft_history(
        db_session,
        icao24="abc123",
        hours=24,
    )

    assert len(result) == 1
    assert result[0]["t"] == recent_ts            