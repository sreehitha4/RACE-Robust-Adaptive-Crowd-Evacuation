
"""Atomic model candidate loading and activation for the live simulation."""

import json
import re
import threading
from pathlib import Path

import numpy as np


MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")


class ModelRegistryError(ValueError):
    """Raised when a model registry operation fails validation."""


class ModelRegistry:
    def __init__(self, model_dir, loader=None):
        self.model_dir = Path(model_dir).resolve()
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.pointer = self.model_dir / "active_model.json"
        self._lock = threading.RLock()

        # Optional injectable loader for tests.
        # Production defaults to the actual RACEPredictor.
        self.loader = loader

        self.active_model = None
        self.active_model_id = None

        self._restore_active_model_id()

    def _restore_active_model_id(self):
        if not self.pointer.is_file():
            return

        try:
            data = json.loads(self.pointer.read_text(encoding="utf-8"))
            model_id = data.get("model_id")

            if isinstance(model_id, str):
                self.active_model_id = f"{model_id}.pth"

        except (OSError, json.JSONDecodeError):
            self.active_model_id = None

    def list(self):
        active = None

        if self.pointer.exists():
            try:
                active = json.loads(
                    self.pointer.read_text(encoding="utf-8")
                ).get("model_id")
            except (OSError, json.JSONDecodeError):
                active = None

        return [
            {
                "model_id": path.stem,
                "active": path.stem == active,
                "bytes": path.stat().st_size,
            }
            for path in sorted(self.model_dir.glob("*.pth"))
        ]

    def _resolve_checkpoint(self, model_id):
        if not isinstance(model_id, str):
            raise ModelRegistryError("Invalid model identifier")

        # Accept both "model_name" and "model_name.pth".
        filename = model_id

        if filename.endswith(".pth"):
            identifier = filename[:-4]
        else:
            identifier = filename
            filename = f"{identifier}.pth"

        # Reject paths, traversal, and unsupported extensions.
        if (
            not MODEL_ID.fullmatch(identifier)
            or "/" in model_id
            or "\\" in model_id
            or model_id in (".", "..")
        ):
            raise ModelRegistryError("Invalid model identifier")

        path = (self.model_dir / filename).resolve()

        if path.parent != self.model_dir or not path.is_file():
            raise FileNotFoundError("Model checkpoint not found")

        return path, identifier, filename

    def _load_candidate(self, path):
        try:
            if self.loader is not None:
                candidate = self.loader(str(path))
            else:
                from simulation_environment.ml.model_inference import (
                    RACEPredictor,
                )

                candidate = RACEPredictor(str(path))

            # Validate inference before changing the active model.
            probe = np.zeros((8, 2), dtype=np.float32)
            result = np.asarray(
                candidate.predict(probe),
                dtype=np.float32,
            )

            if result.shape != (12, 2):
                raise ModelRegistryError(
                    "Candidate model must return predictions with shape (12, 2)"
                )

            if not np.isfinite(result).all():
                raise ModelRegistryError(
                    "Candidate model returned non-finite predictions"
                )

            return candidate

        except ModelRegistryError:
            raise
        except Exception as exc:
            raise ModelRegistryError(
                f"Could not load or validate model: {exc}"
            ) from exc

    def activate(self, model_id, runtime=None):
        path, identifier, filename = self._resolve_checkpoint(model_id)

        # Candidate must load and pass inference validation first.
        candidate = self._load_candidate(path)

        with self._lock:
            temp = self.pointer.with_suffix(".tmp")

            try:
                temp.write_text(
                    json.dumps({"model_id": identifier}),
                    encoding="utf-8",
                )

                # Atomically update the active model pointer.
                temp.replace(self.pointer)

                # Preserve the production runtime activation path.
                if runtime is not None:
                    from server.services.ml_service import MeasuredPredictor

                    runtime.simulation.ml.predictor = MeasuredPredictor(
                        candidate
                    )
                    runtime.simulation.ml.enabled = True

                self.active_model = candidate
                self.active_model_id = filename

            finally:
                temp.unlink(missing_ok=True)

        return {
            "model_id": identifier,
            "status": "active",
            "active": True,
            "device": str(getattr(candidate, "device", "unknown")),
        }
