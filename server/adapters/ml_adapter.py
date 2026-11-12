"""Optional LSTM trajectory prediction with a dependency-free CV fallback."""

import os
from pathlib import Path
from math import isfinite


class TrajectoryPredictionAdapter:
    """Predicts future positions; it does not control simulation movement.

    Set RACE_ML_CHECKPOINT to enable the optional LSTM. Without a checkpoint or
    PyTorch, predictions fall back to constant velocity.
    """

    def __init__(self, checkpoint_path: str | None = None):
        default_path = (
            Path(__file__).resolve().parents[2]
            / "ml" / "models" / "trajectory_lstm_best.pth"
        )
        self.checkpoint_path = Path(
            checkpoint_path or os.getenv("RACE_ML_CHECKPOINT", default_path)
        )
        self._predictor = None
        self._load_error: str | None = None

    @property
    def status(self) -> dict:
        return {
            "available": self._predictor is not None,
            "checkpoint": str(self.checkpoint_path),
            "error": self._load_error,
            "fallback": "constant-velocity",
        }

    def load(self) -> bool:
        if self._predictor is not None:
            return True
        if not self.checkpoint_path.is_file():
            self._load_error = "Checkpoint not found; using constant-velocity fallback."
            return False
        try:
            import sys
            ml_dir = str(self.checkpoint_path.resolve().parents[1])
            if ml_dir not in sys.path:
                sys.path.insert(0, ml_dir)
            from model_inference import RACEPredictor
            self._predictor = RACEPredictor(str(self.checkpoint_path))
            self._load_error = None
            return True
        except Exception as exc:
            self._load_error = f"LSTM unavailable: {exc}"
            self._predictor = None
            return False

    def predict(
        self,
        observed_positions: list[list[float]],
        steps: int = 12,
        interval: float = 0.4,
    ) -> list[list[float]]:
        if len(observed_positions) != 8 or any(len(p) != 2 for p in observed_positions):
            raise ValueError("observed_positions must have shape (8, 2)")
        if not all(
            isinstance(value, (int, float)) and isfinite(value)
            for point in observed_positions for value in point
        ):
            raise ValueError("observed_positions must contain finite numbers")
        if steps < 1 or interval <= 0:
            raise ValueError("steps and interval must be positive")

        if self.load():
            try:
                prediction = self._predictor.predict(observed_positions)
                return [[float(point[0]), float(point[1])] for point in prediction]
            except Exception as exc:
                self._load_error = f"LSTM inference failed; using CV fallback: {exc}"

        last = observed_positions[-1]
        dx = last[0] - observed_positions[-2][0]
        dy = last[1] - observed_positions[-2][1]
        # Eight observed points are assumed to be equally spaced at interval seconds.
        return [
            [float(last[0] + dx * (i + 1)), float(last[1] + dy * (i + 1))]
            for i in range(steps)
        ]
