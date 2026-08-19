from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import OPENSKY_POLL_SECONDS, POSITION_RETENTION_HOURS
from app.database import async_session_factory, engine, get_session
from app.hub import WsHub, parse_bbox_query
from app.opensky import fetch_states, process_states
from app.repository import (
    fetch_aircraft_history,
    fetch_viewport_geojson,
    prune_old_positions
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

hub = WsHub()
_poll_task: asyncio.Task[None] | None = None
_prune_task: asyncio.Task[None] | None = None


async def _poll_opensky_loop() -> None:
    async with httpx.AsyncClient() as client:
        while True:
            try:
                _, states = await fetch_states(client)
                ts = datetime.now(UTC)
                features: list[dict] = []
                async with async_session_factory() as session:
                    features = await process_states(session, states, ts)
                    await session.commit()
                await hub.broadcast_updates(features)
                logger.info("OpenSky ingest: %s features", len(features))
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("OpenSky poll failed")
            await asyncio.sleep(OPENSKY_POLL_SECONDS)


async def _prune_loop() -> None:
    while True:
        try:
            await asyncio.sleep(3600)
            async with async_session_factory() as session:
                await prune_old_positions(session, POSITION_RETENTION_HOURS)
                await session.commit()
                logger.info(
                    "Pruned positions older than %s h", POSITION_RETENTION_HOURS
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Prune task failed")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _poll_task, _prune_task
    _poll_task = asyncio.create_task(_poll_opensky_loop())
    _prune_task = asyncio.create_task(_prune_loop())
    yield
    if _poll_task:
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
    if _prune_task:
        _prune_task.cancel()
        try:
            await _prune_task
        except asyncio.CancelledError:
            pass
    await engine.dispose()


app = FastAPI(title="Geo Tracker API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/live")
async def ws_live(
    websocket: WebSocket,
    min_lon: str | None = Query(None),
    min_lat: str | None = Query(None),
    max_lon: str | None = Query(None),
    max_lat: str | None = Query(None),
):
    bbox = parse_bbox_query(min_lon, min_lat, max_lon, max_lat)
    await hub.connect(websocket, bbox)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") != "bbox":
                continue
            try:
                nb = (
                    float(msg["min_lon"]),
                    float(msg["min_lat"]),
                    float(msg["max_lon"]),
                    float(msg["max_lat"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
            await hub.set_bbox(websocket, nb)
            await websocket.send_json({"type": "bbox_ack", "bbox": nb})
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(websocket)


@app.get("/viewport")
async def viewport(
    min_lon: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lon: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    session: AsyncSession = Depends(get_session),
):
    return await fetch_viewport_geojson(
        session,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
    )

@app.get("/aircraft/{icao24}/history")
async def aircraft_history(
    icao24: str,
    session: AsyncSession = Depends(get_session),
):
    rows = await fetch_aircraft_history(
        session,
        icao24=icao24,
        hours=24,
    )

    coordinates = [
        row["geom"]["coordinates"]
        for row in rows
    ]

    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates,
        },
        "properties": {
            "icao24": icao24,
        },
    }
