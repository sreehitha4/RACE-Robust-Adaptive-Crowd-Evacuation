from __future__ import annotations

import json
import logging
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

logger = logging.getLogger(__name__)
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\.pth$")


class ModelRegistryError(ValueError):
    pass


class ModelRegistry:
    """Versioned model registry with validate-before-activate semantics.

    `loader` must construct a usable predictor from a checkpoint path. The
    default loader integrates with ml/model_inference.py. Tests may inject a
    lightweight loader. The active pointer is persisted with os.replace().
    """

    def __init__(
        self,
        models_dir: str | Path = "ml/weights",
        loader: Callable[[str], Any] | None = None,
    ):
        self.models_dir = Path(models_dir).resolve()
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.pointer_path = self.models_dir / "active_model.json"
        self._loader = loader or self._load_race_predictor
        self._lock = threading.RLock()
        self._active_model = None
        self._active_model_id: str | None = None
        self._load_persisted_active()

    @staticmethod
    def _load_race_predictor(checkpoint_path: str):
        import sys
        checkpoint = Path(checkpoint_path).resolve()
        repo_root = checkpoint.parents[2] if len(checkpoint.parents) > 2 else Path.cwd()
        ml_dir = repo_root / "ml"
        if str(ml_dir) not in sys.path:
            sys.path.insert(0, str(ml_dir))
        try:
            from model_inference import RACEPredictor
        except ImportError as exc:
            raise ModelRegistryError(
                "Could not import RACEPredictor from ml/model_inference.py"
            ) from exc
        return RACEPredictor(str(checkpoint))

    def _validate_model_id(self, model_id: str) -> Path:
        if not MODEL_ID_RE.fullmatch(model_id):
            raise ModelRegistryError("Invalid model_id; expected a .pth checkpoint filename")
        path = (self.models_dir / model_id).resolve()
        if path.parent != self.models_dir or not path.is_file():
            raise FileNotFoundError(f"Model checkpoint '{model_id}' not found")
        return path

    def _load_persisted_active(self) -> None:
        if not self.pointer_path.is_file():
            return
        try:
            payload = json.loads(self.pointer_path.read_text(encoding="utf-8"))
            model_id = payload.get("model_id")
            path = self._validate_model_id(model_id)
            candidate = self._loader(str(path))
            self._active_model = candidate
            self._active_model_id = model_id
        except Exception:
            logger.exception("Persisted active model could not be loaded; no model activated")

    def list_models(self) -> list[dict]:
        with self._lock:
            models = []
            for path in sorted(self.models_dir.glob("*.pth")):
                if not path.is_file():
                    continue
                stat = path.stat()
                models.append({
                    "model_id": path.name,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                    "is_active": path.name == self._active_model_id,
                })
            return models

    def activate(self, model_id: str) -> dict:
        path = self._validate_model_id(model_id)
        if path.stat().st_size == 0:
            raise ModelRegistryError("Checkpoint file is empty")

        # Construct and validate the candidate before touching active state.
        try:
            candidate = self._loader(str(path))
            if candidate is None:
                raise ModelRegistryError("Model loader returned no predictor")
            if not callable(getattr(candidate, "predict", None)):
                raise ModelRegistryError("Loaded model does not expose predict()")
        except Exception as exc:
            raise ModelRegistryError(f"Checkpoint validation failed: {exc}") from exc

        with self._lock:
            previous_model = self._active_model
            previous_id = self._active_model_id
            temp_pointer = self.models_dir / ".active_model.json.tmp"
            payload = {
                "model_id": model_id,
                "activated_at": datetime.now(timezone.utc).isoformat(),
            }
            try:
                with temp_pointer.open("w", encoding="utf-8") as stream:
                    json.dump(payload, stream, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp_pointer, self.pointer_path)
                self._active_model = candidate
                self._active_model_id = model_id
            except Exception:
                temp_pointer.unlink(missing_ok=True)
                self._active_model = previous_model
                self._active_model_id = previous_id
                raise

        return {"model_id": model_id, "previous_model_id": previous_id, "status": "active"}

    @property
    def active_model(self):
        with self._lock:
            return self._active_model

    @property
    def active_model_id(self) -> str | None:
        with self._lock:
            return self._active_model_id

    def predict(self, observed_positions):
        with self._lock:
            model = self._active_model
        if model is None:
            raise ModelRegistryError("No active model is available")
        return model.predict(observed_positions)
