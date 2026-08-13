from datetime import datetime, UTC

import pytest
from sqlalchemy import select

from app.models import Entity, Position
from app.repository import upsert_entity_and_position


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