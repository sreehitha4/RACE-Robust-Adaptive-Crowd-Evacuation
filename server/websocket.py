"""In-process WebSocket fan-out. Redis channel is available for multi-instance deployment."""
import asyncio
import json
from fastapi import WebSocket
from server.observability.metrics import WS_CONNECTIONS, WS_FRAMES

class WebSocketHub:
    def __init__(self):
        self.connections: set[WebSocket] = set()
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.connections.add(websocket)
            WS_CONNECTIONS.set(len(self.connections))

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            self.connections.discard(websocket)
            WS_CONNECTIONS.set(len(self.connections))

    async def send(self, websocket: WebSocket, payload):
        await websocket.send_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))

    async def broadcast(self, payload):
        async with self.lock:
            clients = list(self.connections)
        if not clients:
            return
        encoded = json.dumps(payload, separators=(",", ":"), allow_nan=False)
        results = await asyncio.gather(*(client.send_text(encoded) for client in clients), return_exceptions=True)
        stale = [client for client, result in zip(clients, results) if isinstance(result, Exception)]
        if stale:
            async with self.lock:
                for client in stale:
                    self.connections.discard(client)
                WS_CONNECTIONS.set(len(self.connections))
        if payload.get("type") == "frame":
            WS_FRAMES.inc(len(clients) - len(stale))

hub = WebSocketHub()
