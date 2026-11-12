import io
from pathlib import Path

from fastapi.testclient import TestClient

from server.main import app
from server.services.dataset_service import DatasetService, DatasetValidationError
from server.services.model_registry import ModelRegistry, ModelRegistryError


class FakeUpload:
    def __init__(self, filename, payload):
        self.filename = filename
        self._stream = io.BytesIO(payload)

    async def read(self, size=-1):
        return self._stream.read(size)

    async def close(self):
        self._stream.close()


class FakePredictor:
    def predict(self, observed):
        return [[0.0, 0.0]] * 12


def test_dataset_csv_validation_and_metadata(tmp_path):
    service = DatasetService(tmp_path)
    upload = FakeUpload(
        "walkers.csv",
        b"pedestrian_id,frame,x,y\n1,0,1.0,2.0\n1,1,1.2,2.1\n",
    )
    import asyncio
    result = asyncio.run(service.save_upload(upload))
    assert result["row_count"] == 2
    assert result["status"] == "validated"
    assert len(result["sha256"]) == 64
    assert service.get_dataset_path(result["dataset_id"]).is_file()


def test_dataset_rejects_bad_columns_and_removes_temp_files(tmp_path):
    service = DatasetService(tmp_path)
    upload = FakeUpload("bad.csv", b"id,time,px,py\n1,0,1,2\n")
    import asyncio
    try:
        asyncio.run(service.save_upload(upload))
        assert False, "expected validation error"
    except DatasetValidationError:
        pass
    assert not list(tmp_path.glob("*.csv"))
    assert not list(tmp_path.glob(".*.upload"))


def test_dataset_rejects_path_like_filename(tmp_path):
    service = DatasetService(tmp_path)
    upload = FakeUpload("../../escape.csv", b"pedestrian_id,frame,x,y\n1,0,1,2\n")
    import asyncio
    result = asyncio.run(service.save_upload(upload))
    assert result["filename"] == "escape.csv"
    assert Path(result["stored_filename"]).name == result["stored_filename"]


def test_registry_activates_only_after_candidate_load(tmp_path):
    (tmp_path / "v1.pth").write_bytes(b"checkpoint")
    registry = ModelRegistry(tmp_path, loader=lambda _: FakePredictor())
    result = registry.activate("v1.pth")
    assert result["status"] == "active"
    assert registry.active_model_id == "v1.pth"
    assert registry.active_model is not None
    assert (tmp_path / "active_model.json").is_file()


def test_registry_failed_load_preserves_previous_active_model(tmp_path):
    (tmp_path / "good.pth").write_bytes(b"good")
    (tmp_path / "bad.pth").write_bytes(b"bad")

    def loader(path):
        if path.endswith("bad.pth"):
            raise RuntimeError("incompatible architecture")
        return FakePredictor()

    registry = ModelRegistry(tmp_path, loader=loader)
    registry.activate("good.pth")
    old_model = registry.active_model
    try:
        registry.activate("bad.pth")
        assert False, "expected validation failure"
    except ModelRegistryError:
        pass
    assert registry.active_model_id == "good.pth"
    assert registry.active_model is old_model


def test_registry_rejects_traversal_and_unknown_models(tmp_path):
    registry = ModelRegistry(tmp_path, loader=lambda _: FakePredictor())
    for model_id in ("../outside.pth", "missing.pth", "bad.txt"):
        try:
            registry.activate(model_id)
            assert False, "expected rejection"
        except (ModelRegistryError, FileNotFoundError):
            pass
