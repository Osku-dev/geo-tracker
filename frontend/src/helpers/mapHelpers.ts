import maplibregl from "maplibre-gl";

const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

export function createMap(container: HTMLDivElement) {
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
    new maplibregl.NavigationControl({
      visualizePitch: true,
    }),
    "top-right",
  );

  return map;
}