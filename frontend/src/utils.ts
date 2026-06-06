import { Feature } from "geojson";
import { LngLatBounds } from "maplibre-gl";
import { Aircraft } from "./types/aircraft";

export function boundsParams(b: LngLatBounds): string {
  return new URLSearchParams({
    min_lon: String(b.getWest()),
    min_lat: String(b.getSouth()),
    max_lon: String(b.getEast()),
    max_lat: String(b.getNorth()),
  }).toString();
}

export function upsertFeaturesById(
  existing: Feature[],
  incoming: Feature[],
): Feature[] {
  const map = new Map<string, Feature>();
  for (const f of existing) {
    const id = String((f.properties as Aircraft)?.icao24 ?? "");
    if (id) map.set(id, f);
  }
  for (const f of incoming) {
    const id = String((f.properties as Aircraft)?.icao24 ?? "");
    if (id) map.set(id, f);
  }
  return Array.from(map.values());
}

export function sendBbox(ws: WebSocket, b: LngLatBounds) {
  if (ws.readyState !== WebSocket.OPEN) return;
  ws.send(
    JSON.stringify({
      type: "bbox",
      min_lon: b.getWest(),
      min_lat: b.getSouth(),
      max_lon: b.getEast(),
      max_lat: b.getNorth(),
    }),
  );
}
