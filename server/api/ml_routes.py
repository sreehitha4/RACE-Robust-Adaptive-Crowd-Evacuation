from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/api/v1", tags=["ml"])

class PredictionRequest(BaseModel):
    observed_positions: List[List[float]] = Field(..., min_length=8, max_length=8)

@router.get("/ml/models")
async def list_models(request: Request):
    return {"models": request.app.state.model_registry.list()}

@router.post("/ml/models/{model_id}/activate")
async def activate_model(model_id: str, request: Request):
    try:
        return request.app.state.model_registry.activate(model_id, request.app.state.runtime)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@router.post("/ml/predict")
async def predict(body: PredictionRequest, request: Request):
    runtime = request.app.state.runtime
    if not runtime.simulation.ml.enabled:
        raise HTTPException(status_code=503, detail="ML predictor is not enabled")
    try:
        import numpy as np
        observed = np.asarray(body.observed_positions, dtype=np.float32)
        if observed.shape != (8, 2) or not np.isfinite(observed).all():
            raise ValueError("observed_positions must be finite with shape (8, 2)")
        result = runtime.simulation.ml.predict(observed)
        return {"prediction": np.asarray(result).tolist(), "model": "lstm"}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
