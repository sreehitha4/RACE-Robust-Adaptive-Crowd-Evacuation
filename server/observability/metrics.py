"""Prometheus metrics shared by API, simulation and inference paths."""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

HTTP_REQUESTS = Counter("race_http_requests_total", "HTTP requests", ["method", "path", "status"])
HTTP_LATENCY = Histogram("race_http_request_duration_seconds", "HTTP request duration", ["method", "path"])
WS_CONNECTIONS = Gauge("race_websocket_connections", "Active WebSocket connections")
WS_FRAMES = Counter("race_websocket_frames_total", "Frames sent to WebSocket clients")
SIM_STEP = Histogram("race_simulation_step_seconds", "Simulation step wall time")
SIM_TIME = Gauge("race_simulation_time_seconds", "Current simulated time")
SIM_AGENTS = Gauge("race_simulation_active_agents", "Currently active agents")
SIM_FPS = Gauge("race_simulation_frames_per_second", "Simulation frames emitted per second")
ML_INFERENCE = Histogram("race_ml_inference_seconds", "Trajectory inference duration")
ML_FAILURES = Counter("race_ml_inference_failures_total", "Trajectory inference failures")
ML_FORECAST_ERROR = Histogram("race_ml_one_step_forecast_error", "One-step LSTM forecast error in model coordinate units")
ML_FORECAST_ALERTS = Counter("race_ml_forecast_error_alerts_total", "Forecast errors above configured threshold")
REDIS_PUBLISH_FAILURES = Counter("race_redis_publish_failures_total", "Redis telemetry publish failures")


def render_metrics():
    return generate_latest(), CONTENT_TYPE_LATEST
