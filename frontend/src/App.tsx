import { useRef } from "react";
import { useGeoTrackerMap } from "../src/hooks/useGeoTrackerMap";
import { AircraftPopup } from "./components/AircraftPopup";

export default function App() {
  const containerRef = useRef<HTMLDivElement>(null);

  const { selectedAircraft } = useGeoTrackerMap(containerRef);

  return (
    <div className="map-wrap">
      <div ref={containerRef} className="map" />
      <AircraftPopup aircraft={selectedAircraft} />
    </div>
  );
}
