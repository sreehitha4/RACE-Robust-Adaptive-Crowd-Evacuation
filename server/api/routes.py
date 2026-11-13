
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect

from server.websocket import hub

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    runtime = request.app.state.runtime
    return {
        "status": "ok",
        "simulation_status": runtime.simulation.status,
        "ml_enabled": bool(runtime.simulation.ml.enabled),
        "redis_enabled": bool(runtime.telemetry.client),
        "session_id": runtime.session_id,
    }


@router.get("/ready")
async def ready(request: Request):
    runtime = request.app.state.runtime

    if runtime.simulation is None:
        raise HTTPException(
            status_code=503,
            detail="Simulation is not initialized",
        )

    return {"status": "ready"}


@router.post("/api/simulation/start")
async def start(request: Request):
    runtime = request.app.state.runtime
    frame = await runtime.start()
    return {"status": "running", **frame}


@router.post("/api/simulation/pause")
async def pause(request: Request):
    runtime = request.app.state.runtime
    frame = await runtime.pause()
    return {"status": "paused", **frame}


@router.post("/api/simulation/reset")
async def reset(request: Request):
    runtime = request.app.state.runtime
    frame = await runtime.reset()

    await hub.broadcast(runtime.environment_message())
    await hub.broadcast(runtime.frame())

    return {"status": "reset", **frame}


@router.get("/api/simulation/status")
async def simulation_status(request: Request):
    runtime = request.app.state.runtime
    state = await runtime.snapshot()

    return {
        "status": state["status"],
        "simulation_time": state["simulation_time"],
        "total_agents": len(state["agents"]),
        "evacuated": state["evacuated_count"],
        "ml_enabled": state["ml_enabled"],
        "session_id": runtime.session_id,
        "last_error": runtime.last_error,
    }


@router.get("/api/v1/ml/status")
async def ml_status(request: Request):
    runtime = request.app.state.runtime
    predictor = getattr(runtime.simulation.ml, "predictor", None)
    underlying = getattr(predictor, "predictor", predictor)
    device = getattr(underlying, "device", "unknown")

    return {
        "enabled": bool(runtime.simulation.ml.enabled),
        "backend": runtime.ml_backend,
        "device": str(device),
        "prediction_input": [8, 2],
        "prediction_output": [12, 2],
    }


@router.websocket("/ws/simulation")
async def simulation_socket(websocket: WebSocket):
    await hub.connect(websocket)
    runtime = websocket.app.state.runtime

    try:
        await hub.send(websocket, runtime.environment_message())
        await hub.send(websocket, runtime.frame())

        while True:
            # Controls remain REST-based according to the frontend contract.
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass

    finally:
        # ConnectionManager.disconnect is synchronous.
        hub.disconnect(websocket)
