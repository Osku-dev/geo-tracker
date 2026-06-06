export interface Aircraft {
  icao24: string;
  callsign: string | null;
  origin_country: string;

  baro_altitude_m: number | null;
  velocity_m_s: number | null;
  true_track_deg: number | null;
  vertical_rate_m_s: number | null;

  on_ground: boolean;
  time: string | null;
}