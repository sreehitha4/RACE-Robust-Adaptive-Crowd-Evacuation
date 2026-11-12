from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


def get_manager(request: Request):
    return request.app.state.simulation_manager


@router.post("/simulation/start", tags=["simulation"])
async def start_simulation(request: Request):
    return await get_manager(request).start()


@router.post("/simulation/pause", tags=["simulation"])
async def pause_simulation(request: Request):
    return await get_manager(request).pause()


@router.post("/simulation/reset", tags=["simulation"])
async def reset_simulation(request: Request):
    return await get_manager(request).reset()


@router.get("/simulation/status", tags=["simulation"])
async def simulation_status(request: Request):
    return get_manager(request).status()
