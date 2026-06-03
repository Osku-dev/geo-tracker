import { useRef } from "react";
import { useGeoTrackerMap } from "../src/hooks/useGeoTrackerMap";

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);

  useGeoTrackerMap(containerRef);

  return (
    <div className="map-wrap">
      <div ref={containerRef} className="map" />
    </div>
  );
}
