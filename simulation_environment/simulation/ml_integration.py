from pathlib import Path
import numpy as np

class MLTrajectoryAdapter:
    """Optional adapter for Sreehitha's RACEPredictor. No fallback predictions are fabricated."""
    def __init__(self, checkpoint_path=None, predictor=None):
        self.predictor = predictor
        self.enabled = predictor is not None
        if predictor is None and checkpoint_path:
            path = Path(checkpoint_path)
            if path.exists():
                # Import from the teammate's unchanged inference implementation.
                import sys
                ml_dir = str(path.parent.parent.resolve())
                if ml_dir not in sys.path:
                    sys.path.insert(0, ml_dir)
                from model_inference import RACEPredictor
                self.predictor = RACEPredictor(str(path))
                self.enabled = True

    def predict(self, observed_positions):
        if not self.enabled:
            return None
        observed = np.asarray(observed_positions, dtype=np.float32)
        if observed.shape != (8, 2):
            raise ValueError(f"RACEPredictor requires (8, 2), got {observed.shape}")
        result = np.asarray(self.predictor.predict(observed), dtype=np.float32)
        if result.shape != (12, 2) or not np.isfinite(result).all():
            raise ValueError(f"RACEPredictor must return finite (12, 2), got {result.shape}")
        return result
