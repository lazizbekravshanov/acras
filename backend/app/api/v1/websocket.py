"""WebSocket endpoint for real-time incident updates."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory connection manager — tracks all active WS clients
_connections: set[WebSocket] = set()


async def broadcast(message: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    payload = json.dumps(message, default=str)
    dead = set()
    for ws in _connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for live dashboard updates."""
    await ws.accept()
    _connections.add(ws)
    logger.info("WebSocket client connected. Total: %d", len(_connections))

    try:
        while True:
            # Keep connection alive; handle client messages if needed
            data = await ws.receive_text()
            # Clients can send ping or subscribe to specific feeds
            if data == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(ws)
        logger.info("WebSocket client disconnected. Total: %d", len(_connections))
