import io
import pytest
from starlette.datastructures import UploadFile
from server.services.dataset_service import DatasetService, DatasetValidationError

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_dataset_upload_and_metadata(tmp_path):
    service = DatasetService(tmp_path)
    upload = UploadFile(filename="tracks.csv", file=io.BytesIO(b"pedestrian_id,frame,x,y\n1,0,1.2,2.3\n"))
    result = await service.save(upload)
    assert result["rows"] == 1
    assert result["sha256"]
    assert service.list()[0]["dataset_id"] == result["dataset_id"]

@pytest.mark.anyio
async def test_dataset_rejects_wrong_schema(tmp_path):
    service = DatasetService(tmp_path)
    upload = UploadFile(filename="tracks.csv", file=io.BytesIO(b"id,x,y\n1,2,3\n"))
    with pytest.raises(DatasetValidationError):
        await service.save(upload)
    assert not list(tmp_path.glob("*.csv"))
