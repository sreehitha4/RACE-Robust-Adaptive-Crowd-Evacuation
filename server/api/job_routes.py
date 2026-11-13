from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.get("/{job_id}")
async def job_status(job_id: str):
    try:
        from server.workers.celery_app import celery_app
        result = celery_app.AsyncResult(job_id)
        payload = {"job_id": job_id, "status": result.status.lower()}
        if result.successful(): payload["result"] = result.result
        elif result.failed(): payload["error"] = str(result.result)
        return payload
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Worker result backend unavailable: {exc}")
