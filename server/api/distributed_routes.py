from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/simulation", tags=["distributed-simulation"])

class BatchRequest(BaseModel):
    overrides: Dict[str, Any] = Field(default_factory=dict)
    steps: int = Field(default=100, ge=1, le=100000)

@router.post("/batch")
async def submit_batch(body: BatchRequest, request: Request):
    from dataclasses import asdict
    from server.workers.ray_tasks import submit_scenario
    config = asdict(request.app.state.runtime.config)
    allowed = set(config)
    unknown = set(body.overrides) - allowed
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown config keys: {', '.join(sorted(unknown))}")
    config.update(body.overrides)
    try:
        ref = submit_scenario(config, body.steps)
        job_id = ref.hex()
        request.app.state.ray_jobs[job_id] = ref
        return {"job_id": job_id, "status": "submitted", "execution": "ray"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

@router.get("/batch/{job_id}")
async def batch_status(job_id: str, request: Request):
    ref = request.app.state.ray_jobs.get(job_id)
    if ref is None:
        raise HTTPException(status_code=404, detail="Unknown batch job")
    import ray
    if not ray.wait([ref], timeout=0)[0]:
        return {"job_id": job_id, "status": "running"}
    try:
        result = ray.get(ref)
        return {"job_id": job_id, "status": "completed", "result": result}
    except Exception as exc:
        return {"job_id": job_id, "status": "failed", "error": str(exc)}
