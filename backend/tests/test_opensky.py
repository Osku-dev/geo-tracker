from app.opensky import state_to_feature


def test_state_to_feature_returns_geojson_feature():
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


def test_state_to_feature_strips_and_lowercases_icao24():
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


def test_state_to_feature_strips_callsign_and_handles_empty_string():
    row = [
        "ABC123",
        "   ",  # becomes empty after strip -> None
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


def test_state_to_feature_returns_none_for_empty_row():
    assert state_to_feature([]) is None
    assert state_to_feature(None) is None


def test_state_to_feature_returns_none_for_short_row():
    row = ["ABC123", "FIN123"]
    assert state_to_feature(row) is None


def test_state_to_feature_returns_none_when_icao24_missing():
    row = [
        None,  # missing ICAO24
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


def test_state_to_feature_returns_none_when_coordinates_missing():
    row = [
        "ABC123",
        "FIN123",
        "Finland",
        None,
        None,
        None,  # lon missing
        None,  # lat missing
        11000,
        False,
        250,
        180,
    ]

    assert state_to_feature(row) is None


def test_state_to_feature_handles_optional_vertical_rate():
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
        None,  # vertical rate explicitly None
    ]

    result = state_to_feature(row)

    assert result["properties"]["vertical_rate_m_s"] is None