from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from server.adapters.mock_simulation import MockSimulationAdapter
from server.api.routes import router
from server.api.ml_lifecycle import router as ml_lifecycle_router
from server.services.dataset_service import DatasetService
from server.services.model_registry import ModelRegistry
from server.core.manager import SimulationManager
from server.websocket.manager import ConnectionManager

connections = ConnectionManager()
simulation = SimulationManager(
    adapter=MockSimulationAdapter(),
    connections=connections,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Services are initialized once per process; paths are configurable later.
    app.state.dataset_service = DatasetService(
        upload_dir=Path.cwd() / "data" / "processed"
    )
    app.state.model_registry = ModelRegistry(
        models_dir=Path.cwd() / "ml" / "weights"
    )
    yield
    await simulation.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="RACE Backend API",
    version="0.1.0",
    description="Backend integration layer for the RACE crowd simulation project.",
)
app.state.simulation_manager = simulation

# Vite proxies /api and /ws during development. This also permits direct local use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(ml_lifecycle_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "race-backend"}


@app.websocket("/ws/simulation")
async def simulation_stream(websocket: WebSocket):
    await connections.connect(websocket)
    try:
        # Contract: each new client receives environment first, then current frame.
        await simulation.send_initial_state(websocket)
        while True:
            # The current frontend sends no commands over this socket. Receiving
            # lets Starlette detect client disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connections.disconnect(websocket)

