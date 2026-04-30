import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by session_id."""

    def __init__(self):
        # session_id → WebSocket
        self._connections: dict[int, WebSocket] = {}

    async def connect(self, session_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id] = websocket
        logger.info("WS connected: session %d", session_id)

    def disconnect(self, session_id: int) -> None:
        self._connections.pop(session_id, None)
        logger.info("WS disconnected: session %d", session_id)

    async def send(self, session_id: int, data: dict) -> None:
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning("WS send failed for session %d: %s", session_id, e)
                self.disconnect(session_id)

    def is_connected(self, session_id: int) -> bool:
        return session_id in self._connections


# Singleton — imported by the WS router and live pipeline
manager = ConnectionManager()
