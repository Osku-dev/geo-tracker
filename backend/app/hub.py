from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _point_in_bbox(
    lon: float, lat: float, bbox: tuple[float, float, float, float]
) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def parse_bbox_query(
    min_lon: str | None,
    min_lat: str | None,
    max_lon: str | None,
    max_lat: str | None,
) -> tuple[float, float, float, float] | None:
    if min_lon is None or min_lat is None or max_lon is None or max_lat is None:
        return None
    try:
        return (
            float(min_lon),
            float(min_lat),
            float(max_lon),
            float(max_lat),
        )
    except ValueError:
        return None


class WsHub:
    """Fan-out GeoJSON features to WebSocket clients with optional bbox filtering."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._clients: dict[WebSocket, tuple[float, float, float, float] | None] = {}

    async def connect(
        self,
        websocket: WebSocket,
        bbox: tuple[float, float, float, float] | None,
    ) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients[websocket] = bbox

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.pop(websocket, None)

    async def set_bbox(
        self,
        websocket: WebSocket,
        bbox: tuple[float, float, float, float] | None,
    ) -> None:
        async with self._lock:
            if websocket in self._clients:
                self._clients[websocket] = bbox

    def _filter_features(
        self,
        features: list[dict[str, Any]],
        bbox: tuple[float, float, float, float] | None,
    ) -> list[dict[str, Any]]:
        if bbox is None:
            return features
        out: list[dict[str, Any]] = []
        for f in features:
            coords = f.get("geometry", {}).get("coordinates")
            if not coords or len(coords) < 2:
                continue
            lon, lat = float(coords[0]), float(coords[1])
            if _point_in_bbox(lon, lat, bbox):
                out.append(f)
        return out

    async def broadcast_updates(self, features: list[dict[str, Any]]) -> None:
        if not features:
            return
        async with self._lock:
            snapshot = dict(self._clients)
        dead: list[WebSocket] = []
        payload_base = {"type": "updates"}
        for ws, bbox in snapshot.items():
            filtered = self._filter_features(features, bbox)
            if not filtered:
                continue
            message = {**payload_base, "features": filtered}
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                logger.debug("WS send failed; dropping client")
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.pop(ws, None)
