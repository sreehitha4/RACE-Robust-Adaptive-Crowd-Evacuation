import asyncio

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class ConnectionManager:
    """Tracks browser clients and broadcasts frontend-contract messages."""

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        async with self._lock:
            clients = list(self._connections)

        stale: list[WebSocket] = []
        for client in clients:
            try:
                if client.client_state == WebSocketState.CONNECTED:
                    await client.send_json(message)
                else:
                    stale.append(client)
            except Exception:
                stale.append(client)

        for client in stale:
            self.disconnect(client)

    async def send(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_json(message)

    @property
    def client_count(self) -> int:
        return len(self._connections)
