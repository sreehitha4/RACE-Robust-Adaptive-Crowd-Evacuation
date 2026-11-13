from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from server.services.dataset_service import DatasetValidationError

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])

@router.post("/upload")
async def upload_dataset(request: Request, file: UploadFile = File(...)):
    try:
        return await request.app.state.dataset_service.save(file)
    except DatasetValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        await file.close()

@router.get("")
async def list_datasets(request: Request):
    return {"datasets": request.app.state.dataset_service.list()}

@router.post("/{dataset_id}/validate-async")
async def validate_dataset_async(dataset_id: str, request: Request):
    import re
    from pathlib import Path
    if not re.fullmatch(r"[a-f0-9]{32}", dataset_id):
        raise HTTPException(status_code=422, detail="Invalid dataset identifier")
    dataset_path = request.app.state.dataset_service.directory / f"{dataset_id}.csv"
    if not dataset_path.is_file():
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        from server.workers.tasks import validate_dataset
        result = validate_dataset.delay(str(dataset_path.resolve()))
        return {"job_id": result.id, "status": "queued", "queue": "celery"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Background worker unavailable: {exc}")
