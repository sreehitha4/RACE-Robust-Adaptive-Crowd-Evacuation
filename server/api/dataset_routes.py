from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from server.services.dataset_service import DatasetValidationError

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("/upload", status_code=201)
async def upload_dataset(request: Request, file: UploadFile = File(...)):
    service = request.app.state.dataset_service
    try:
        metadata = await service.save_upload(file)
        return {"message": "Dataset validated and stored", "dataset": metadata}
    except DatasetValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Dataset storage failed") from exc


@router.get("")
async def list_datasets(request: Request):
    return {"datasets": request.app.state.dataset_service.list_datasets()}
