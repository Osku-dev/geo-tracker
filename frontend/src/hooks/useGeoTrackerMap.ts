import type { Feature, FeatureCollection } from "geojson";
import maplibregl, { type LngLatBounds } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { boundsParams, sendBbox, upsertFeaturesById } from "../utils";

const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

const apiBase = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const wsBase = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/ws/live";
const terrainTileJson = import.meta.env.VITE_TERRAIN_TILEJSON;

export function useGeoTrackerMap(
  containerRef: React.RefObject<HTMLDivElement>,
) {
  const wsRef = useRef<WebSocket | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fcRef = useRef<FeatureCollection>({
    type: "FeatureCollection",
    features: [],
  });

  const [selectedAircraft, setSelectedAircraft] = useState<Record<
    string,
    unknown
  > | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = createMap(containerRef.current);

    const syncSource = () => {
      const src = map.getSource("traffic") as
        | maplibregl.GeoJSONSource
        | undefined;
      if (src) src.setData(fcRef.current);
    };

    async function loadViewport() {
      const b = map.getBounds();
      const q = boundsParams(b);
      try {
        const r = await fetch(`${apiBase}/viewport?${q}`);
        if (!r.ok) throw new Error(await r.text());
        const data = (await r.json()) as FeatureCollection;
        fcRef.current.features = upsertFeaturesById(
          fcRef.current.features,
          data.features as Feature[],
        );
        syncSource();
      } catch (e) {
        console.error("viewport fetch failed", e);
      }
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
          fcRef.current.features = upsertFeaturesById(
            fcRef.current.features,
            msg.features,
          );
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
        data: fcRef.current,
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

      map.on("click", "traffic-core", (e) => {
        const feature = e.features?.[0];
        if (!feature) return;

        setSelectedAircraft(feature.properties as Record<string, unknown>);
      });

      map.on("mouseenter", "traffic-core", () => {
        map.getCanvas().style.cursor = "pointer";
      });

      map.on("mouseleave", "traffic-core", () => {
        map.getCanvas().style.cursor = "";
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
   return {
    selectedAircraft,
  };
}

function createMap(container: HTMLDivElement) {
  const map = new maplibregl.Map({
    container,
    style: STYLE_URL,
    center: [10.45, 51.16],
    zoom: 5,
    pitch: 52,
    bearing: -12,
    maxPitch: 85,
  });

  map.addControl(
    new maplibregl.NavigationControl({ visualizePitch: true }),
    "top-right",
  );

  return map;
}
