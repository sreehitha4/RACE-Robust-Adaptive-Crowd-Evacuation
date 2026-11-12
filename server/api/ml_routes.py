from fastapi import APIRouter, HTTPException, Request

from server.services.model_registry import ModelRegistryError

router = APIRouter(prefix="/api/v1/ml", tags=["machine-learning"])


@router.get("/models")
async def list_models(request: Request):
    registry = request.app.state.model_registry
    return {
        "models": registry.list_models(),
        "active_model_id": registry.active_model_id,
    }


@router.post("/models/{model_id}/activate")
async def activate_model(model_id: str, request: Request):
    registry = request.app.state.model_registry
    try:
        result = registry.activate(model_id)
        return {"success": True, **result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelRegistryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
