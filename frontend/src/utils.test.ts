import { describe, test, expect } from "vitest";
import { LngLatBounds } from "maplibre-gl";
import { boundsParams, upsertFeaturesById } from "./utils";
import { Feature } from "geojson";

describe("boundsParams", () => {
  test("creates query parameters from bounds", () => {
    const bounds = new LngLatBounds(
      [20, 60], // west, south
      [30, 70], // east, north
    );

    expect(boundsParams(bounds)).toBe(
      "min_lon=20&min_lat=60&max_lon=30&max_lat=70",
    );
  });

  test("handles decimal coordinates", () => {
    const bounds = new LngLatBounds([24.9384, 60.1699], [25.1234, 60.4567]);

    expect(boundsParams(bounds)).toBe(
      "min_lon=24.9384&min_lat=60.1699&max_lon=25.1234&max_lat=60.4567",
    );
  });
});

describe("upsertFeaturesById", () => {
  test("adds new features", () => {
    const existing: Feature[] = [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [10, 60],
        },
        properties: {
          icao24: "abc123",
          callsign: "FIN123",
        },
      },
    ];

    const incoming: Feature[] = [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [10, 60],
        },
        properties: {
          icao24: "def456",
          callsign: "SAS456",
        },
      },
    ];

    const result = upsertFeaturesById(existing, incoming);

    expect(result).toHaveLength(2);
  });

  test("replaces existing feature with matching icao24", () => {
    const existing: Feature[] = [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [10, 60],
        },
        properties: {
          icao24: "abc123",
          callsign: "OLD",
        },
      },
    ];

    const incoming: Feature[] = [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [10, 60],
        },
        properties: {
          icao24: "abc123",
          callsign: "NEW",
        },
      },
    ];

    const result = upsertFeaturesById(existing, incoming);

    expect(result).toHaveLength(1);
    expect(result[0].properties?.callsign).toBe("NEW");
  });

  test("ignores features without icao24", () => {
    const existing: Feature[] = [];

    const incoming: Feature[] = [
      {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [10, 60],
        },
        properties: {
          callsign: "UNKNOWN",
        },
      },
    ];

    const result = upsertFeaturesById(existing, incoming);

    expect(result).toHaveLength(0);
  });
});
