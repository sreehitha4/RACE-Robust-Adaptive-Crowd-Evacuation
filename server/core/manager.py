import asyncio

from fastapi import WebSocket

from server.adapters.base import SimulationAdapter
from server.websocket.manager import ConnectionManager


class SimulationManager:
    def __init__(
        self,
        adapter: SimulationAdapter,
        connections: ConnectionManager,
        frame_rate: float = 10.0,
    ):
        if frame_rate <= 0:
            raise ValueError("frame_rate must be positive")
        self.adapter = adapter
        self.connections = connections
        self.frame_rate = frame_rate
        self.running = False
        self._loop_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    def _environment_dict(self) -> dict:
        return self.adapter.environment().model_dump(mode="json")

    def _frame_dict(self) -> dict:
        return self.adapter.frame().model_dump(mode="json")

    async def send_initial_state(self, websocket: WebSocket) -> None:
        await self.connections.send(websocket, self._environment_dict())
        await self.connections.send(websocket, self._frame_dict())

    async def _broadcast_initial_state(self) -> None:
        await self.connections.broadcast(self._environment_dict())
        await self.connections.broadcast(self._frame_dict())

    async def start(self) -> dict:
        async with self._lock:
            if self.running:
                return {"status": "running"}
            self.running = True
            if self._loop_task is None or self._loop_task.done():
                self._loop_task = asyncio.create_task(self._run_loop())
        return {"status": "running"}

    async def pause(self) -> dict:
        async with self._lock:
            self.running = False
        return {"status": "paused"}

    async def reset(self) -> dict:
        async with self._lock:
            self.running = False
            self.adapter.reset()
        await self._broadcast_initial_state()
        return {"status": "reset"}

    async def _run_loop(self) -> None:
        interval = 1.0 / self.frame_rate
        try:
            while True:
                await asyncio.sleep(interval)
                if not self.running:
                    continue
                self.adapter.step(interval)
                await self.connections.broadcast(self._frame_dict())
        except asyncio.CancelledError:
            raise

    async def shutdown(self) -> None:
        self.running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

    def status(self) -> dict:
        return {
            "status": "running" if self.running else "paused",
            "connected_clients": self.connections.client_count,
            "frame_rate": self.frame_rate,
            "simulation_time": self.adapter.frame().simulation_time,
        }
