import { Aircraft } from "../types/aircraft";
import "./AircraftPopup.css";

type Props = {
  aircraft: Aircraft | null;
};

export function AircraftPopup({ aircraft }: Props) {
  if (!aircraft) return null;

  return (
    <div className={"aircraft-popup"}>
      <h3>{String(aircraft.callsign ?? "Unknown")}</h3>

      <div>ICAO24: {String(aircraft.icao24)}</div>
      <div>Country: {String(aircraft.origin_country)}</div>
      <div>Altitude: {String(aircraft.baro_altitude_m)} m</div>
      <div>Speed: {String(aircraft.velocity_m_s)} m/s</div>
      <div>Track: {String(aircraft.true_track_deg)}°</div>
      <div>
        Ground:
        {aircraft.on_ground ? " Yes" : " No"}
      </div>
    </div>
  );
}