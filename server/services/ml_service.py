"""Thin, measured adapter around the simulation-owned LSTM predictor."""
import logging
import time
from server.observability.metrics import ML_INFERENCE, ML_FAILURES
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("race.ml")

class MeasuredPredictor:
    def __init__(self, predictor):
        self.predictor = predictor

    def predict(self, observed_positions):
        started = time.perf_counter()
        try:
            with tracer.start_as_current_span("race.ml.inference"):
                return self.predictor.predict(observed_positions)
        except Exception:
            ML_FAILURES.inc()
            logger.exception("Trajectory inference failed")
            raise
        finally:
            ML_INFERENCE.observe(time.perf_counter() - started)
