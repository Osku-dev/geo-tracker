from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.repository import upsert_entity_and_position
from app.models import Position


@pytest.mark.asyncio
class TestUpsertEntityAndPosition:

    async def test_returns_geojson_feature(self):
        session = AsyncMock()
        session.add = Mock()
        ts = datetime(2025, 1, 1, tzinfo=UTC)

        result = await upsert_entity_and_position(
            session,
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

        assert result == {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [24.94, 60.17],
            },
            "properties": {
                "icao24": "abc123",
                "callsign": "FIN123",
                "origin_country": "Finland",
                "baro_altitude_m": 1000,
                "on_ground": False,
                "velocity_m_s": 250,
                "true_track_deg": 180,
                "vertical_rate_m_s": 5,
                "time": ts.isoformat(),
            },
        }

    async def test_adds_position_to_session(self):
        session = AsyncMock()
        session.add = Mock()
        ts = datetime.now(timezone.utc)

        await upsert_entity_and_position(
            session,
            icao24="abc123",
            callsign="FIN123",
            origin_country="Finland",
            lon=24.94,
            lat=60.17,
            baro_altitude_m=1000,
            velocity_m_s=200,
            true_track_deg=180,
            vertical_rate_m_s=5,
            on_ground=False,
            ts=ts,
        )

        session.add.assert_called_once()

        position = session.add.call_args.args[0]
        assert isinstance(position, Position)
        assert position.icao24 == "abc123"
        assert position.on_ground is False

    async def test_executes_entity_upsert(self):
        session = AsyncMock()
        session.add = Mock()
        ts = datetime.now(UTC)
        
        await upsert_entity_and_position(
                session,
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
        
        session.execute.assert_called_once()
    