-- PostGIS schema for flight / entity tracking
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE entities (
    icao24 TEXT PRIMARY KEY,
    callsign TEXT,
    origin_country TEXT,
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    icao24 TEXT NOT NULL REFERENCES entities (icao24) ON DELETE CASCADE,
    t TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    geom geometry(Point, 4326) NOT NULL,
    baro_altitude_m DOUBLE PRECISION,
    velocity_m_s DOUBLE PRECISION,
    true_track_deg DOUBLE PRECISION,
    vertical_rate_m_s DOUBLE PRECISION,
    on_ground BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_positions_icao24_t ON positions (icao24, t DESC);
CREATE INDEX idx_positions_geom ON positions USING GIST (geom);
CREATE INDEX idx_positions_t ON positions (t DESC);

COMMENT ON TABLE entities IS 'Stable aircraft / entity ids (e.g. ICAO24 hex)';
COMMENT ON TABLE positions IS 'Time-series positions; prune old rows via app retention task';
