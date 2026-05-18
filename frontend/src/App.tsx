import type { Feature, FeatureCollection } from "geojson";
import maplibregl, { type LngLatBounds } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

const apiBase = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const wsBase = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/ws/live";
const terrainTileJson = import.meta.env.VITE_TERRAIN_TILEJSON;

function boundsParams(b: LngLatBounds): string {
  return new URLSearchParams({
    min_lon: String(b.getWest()),
    min_lat: String(b.getSouth()),
    max_lon: String(b.getEast()),
    max_lat: String(b.getNorth()),
  }).toString();
}

function mergeFeatures(existing: Feature[], incoming: Feature[]): Feature[] {
  const map = new Map<string, Feature>();
  for (const f of existing) {
    const id = String((f.properties as Record<string, unknown>)?.icao24 ?? "");
    if (id) map.set(id, f);
  }
  for (const f of incoming) {
    const id = String((f.properties as Record<string, unknown>)?.icao24 ?? "");
    if (id) map.set(id, f);
  }
  return Array.from(map.values());
}

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: [10.45, 51.16],
      zoom: 5,
      pitch: 52,
      bearing: -12,
      maxPitch: 85,
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    const fcRef: FeatureCollection = { type: "FeatureCollection", features: [] };

    const syncSource = () => {
      const src = map.getSource("traffic") as maplibregl.GeoJSONSource | undefined;
      if (src) src.setData(fcRef);
    };

    async function loadViewport() {
      const b = map.getBounds();
      const q = boundsParams(b);
      try {
        const r = await fetch(`${apiBase}/viewport?${q}`);
        if (!r.ok) throw new Error(await r.text());
        const data = (await r.json()) as FeatureCollection;
        fcRef.features = mergeFeatures(fcRef.features, data.features as Feature[]);
        syncSource();
      } catch (e) {
        console.error("viewport fetch failed", e);
      }
    }

    function sendBbox(ws: WebSocket, b: LngLatBounds) {
      if (ws.readyState !== WebSocket.OPEN) return;
      ws.send(
        JSON.stringify({
          type: "bbox",
          min_lon: b.getWest(),
          min_lat: b.getSouth(),
          max_lon: b.getEast(),
          max_lat: b.getNorth(),
        })
      );
    }

    function connectWs(b: LngLatBounds) {
      wsRef.current?.close();
      const wsUrl = `${wsBase}?${boundsParams(b)}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data as string) as {
            type?: string;
            features?: Feature[];
          };
          if (msg.type !== "updates" || !msg.features?.length) return;
          fcRef.features = mergeFeatures(fcRef.features, msg.features);
          syncSource();
        } catch {
          /* ignore */
        }
      };
      ws.onopen = () => sendBbox(ws, map.getBounds());
    }

    function scheduleViewportAndBbox() {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        const b = map.getBounds();
        void loadViewport();
        const ws = wsRef.current;
        if (ws?.readyState === WebSocket.OPEN) sendBbox(ws, b);
        else if (!ws || ws.readyState === WebSocket.CLOSED) connectWs(b);
      }, 320);
    }

    map.on("load", () => {
      if (terrainTileJson) {
        map.addSource("terrain-rgb", {
          type: "raster-dem",
          url: terrainTileJson,
          tileSize: 256,
        });
        map.setTerrain({ source: "terrain-rgb", exaggeration: 1.25 });
      }

      map.addSource("traffic", {
        type: "geojson",
        data: fcRef,
        promoteId: "icao24",
      });

      map.addLayer({
        id: "traffic-glow",
        type: "circle",
        source: "traffic",
        paint: {
          "circle-radius": 10,
          "circle-color": "#38bdf8",
          "circle-opacity": 0.25,
          "circle-blur": 0.8,
        },
      });

      map.addLayer({
        id: "traffic-core",
        type: "circle",
        source: "traffic",
        paint: {
          "circle-radius": 5,
          "circle-color": [
            "case",
            ["==", ["get", "on_ground"], true],
            "#94a3b8",
            "#f97316",
          ],
          "circle-opacity": 0.92,
          "circle-stroke-width": 1,
          "circle-stroke-color": "#0f172a",
        },
      });

      const initialB = map.getBounds();
      connectWs(initialB);
      void loadViewport();
    });

    map.on("moveend", scheduleViewportAndBbox);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      wsRef.current?.close();
      wsRef.current = null;
      map.remove();
    };
  }, []);

  return (
    <div className="map-wrap">
      <div ref={containerRef} className="map" />
      <div className="hud">
        <strong>Geo Tracker</strong>
        <div>OpenSky feed via FastAPI + PostGIS. Pan/zoom to refresh the viewport.</div>
        <div>
          API <code>{apiBase}</code> · WS <code>{wsBase}</code>
        </div>
      </div>
    </div>
  );
}
