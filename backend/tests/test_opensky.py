from unittest.mock import patch

from app.opensky import state_to_feature, state_to_model_fields


class TestStateToFeature:

    def test_returns_geojson_feature(self):
        row = [
            "ABC123 ",
            " FIN123 ",
            "Finland",
            None,
            None,
            24.94,
            60.17,
            11000,
            False,
            250,
            180,
            5,
        ]

        result = state_to_feature(row)

        assert result is not None
        assert result["type"] == "Feature"
        assert result["geometry"]["type"] == "Point"
        assert result["geometry"]["coordinates"] == [24.94, 60.17]

        props = result["properties"]
        assert props["icao24"] == "abc123"
        assert props["callsign"] == "FIN123"
        assert props["origin_country"] == "Finland"
        assert props["baro_altitude_m"] == 11000
        assert props["on_ground"] is False
        assert props["velocity_m_s"] == 250
        assert props["true_track_deg"] == 180
        assert props["vertical_rate_m_s"] == 5

    def test_strips_and_lowercases_icao24(self):
        row = [
            "  AbC123  ",
            "FIN123",
            "Finland",
            None,
            None,
            24.0,
            60.0,
            1000,
            False,
            100,
            90,
            1,
        ]

        result = state_to_feature(row)

        assert result["properties"]["icao24"] == "abc123"

    def test_strips_callsign_and_handles_empty_string(self):
        row = [
            "ABC123",
            "   ",
            "Finland",
            None,
            None,
            24.0,
            60.0,
            1000,
            False,
            100,
            90,
            1,
        ]

        result = state_to_feature(row)

        assert result["properties"]["callsign"] is None

    def test_returns_none_for_empty_row(self):
        assert state_to_feature([]) is None
        assert state_to_feature(None) is None

    def test_returns_none_for_short_row(self):
        row = ["ABC123", "FIN123"]
        assert state_to_feature(row) is None

    def test_returns_none_when_icao24_missing(self):
        row = [
            None,
            "FIN123",
            "Finland",
            None,
            None,
            24.94,
            60.17,
            11000,
            False,
            250,
            180,
            5,
        ]

        assert state_to_feature(row) is None

    def test_returns_none_when_coordinates_missing(self):
        row = [
            "ABC123",
            "FIN123",
            "Finland",
            None,
            None,
            None,
            None,
            11000,
            False,
            250,
            180,
        ]

        assert state_to_feature(row) is None

    def test_handles_optional_vertical_rate(self):
        row = [
            "ABC123",
            "FIN123",
            "Finland",
            None,
            None,
            24.94,
            60.17,
            11000,
            False,
            250,
            180,
            None,
        ]

        result = state_to_feature(row)

        assert result["properties"]["vertical_rate_m_s"] is None


class TestStateToModelFields:

    MOCK_FEATURE = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [24.9384, 60.1699],
        },
        "properties": {
            "icao24": "abc123",
            "callsign": "test123",
            "origin_country": "Finland",
            "baro_altitude_m": 1200,
            "on_ground": False,
            "velocity_m_s": 55.5,
            "true_track_deg": 180,
            "vertical_rate_m_s": 2.5,
        },
    }

    def test_returns_flattened_model_fields(self):
        row = ["fake_row"]

        with patch("app.opensky.state_to_feature", return_value=self.MOCK_FEATURE):
            result = state_to_model_fields(row)

        assert result == {
            "icao24": "abc123",
            "callsign": "test123",
            "origin_country": "Finland",
            "lon": 24.9384,
            "lat": 60.1699,
            "baro_altitude_m": 1200,
            "on_ground": False,
            "velocity_m_s": 55.5,
            "true_track_deg": 180,
            "vertical_rate_m_s": 2.5,
        }

    def test_returns_none_when_feature_invalid(self):
        row = ["fake_row"]

        with patch("app.opensky.state_to_feature", return_value=None):
            result = state_to_model_fields(row)

        assert result is None