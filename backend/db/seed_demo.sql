-- Optional: manual demo points (run after DB is up). Example:
--   docker compose exec -T db psql -U tracker -d tracker -f - < backend/db/seed_demo.sql
-- Or copy SQL into psql.

INSERT INTO entities (icao24, callsign, origin_country, last_seen)
VALUES ('abcdef', 'DEMO1 ', 'XX', NOW())
ON CONFLICT (icao24) DO UPDATE SET
  callsign = EXCLUDED.callsign,
  last_seen = EXCLUDED.last_seen;

INSERT INTO positions (icao24, t, geom, baro_altitude_m, velocity_m_s, true_track_deg, vertical_rate_m_s, on_ground)
VALUES (
  'abcdef',
  NOW(),
  ST_SetSRID(ST_MakePoint(10.45, 51.16), 4326),
  3200,
  180,
  85,
  -2.5,
  FALSE
);

INSERT INTO entities (icao24, callsign, origin_country, last_seen)
VALUES ('a1b2c3', 'DEMO2 ', 'YY', NOW())
ON CONFLICT (icao24) DO UPDATE SET
  callsign = EXCLUDED.callsign,
  last_seen = EXCLUDED.last_seen;

INSERT INTO positions (icao24, t, geom, baro_altitude_m, velocity_m_s, true_track_deg, vertical_rate_m_s, on_ground)
VALUES (
  'a1b2c3',
  NOW(),
  ST_SetSRID(ST_MakePoint(10.52, 51.22), 4326),
  8100,
  210,
  265,
  0,
  FALSE
);
