"""Optional ONNX Runtime implementation of the RACE (8,2)->(12,2) predictor."""
import numpy as np

class OnnxRACEPredictor:
    def __init__(self, model_path, providers=None):
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("Install onnxruntime to use RACE_ML_BACKEND=onnx") from exc
        self.session = ort.InferenceSession(str(model_path), providers=providers or ["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.device = "onnxruntime"

    def predict(self, observed_positions):
        positions = np.asarray(observed_positions, dtype=np.float32)
        if positions.shape != (8, 2) or not np.isfinite(positions).all():
            raise ValueError("Expected finite observed_positions with shape (8, 2)")
        origin = positions[-1].copy()
        normalized = (positions-origin)[None, ...]
        result = self.session.run([self.output_name], {self.input_name: normalized})[0]
        prediction = np.asarray(result, dtype=np.float32).reshape(12, 2) + origin
        if not np.isfinite(prediction).all():
            raise ValueError("ONNX model returned non-finite predictions")
        return prediction
