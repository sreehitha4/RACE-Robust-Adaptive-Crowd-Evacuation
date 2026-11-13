"""Owns the live simulation lifecycle and serializes state mutations."""
import asyncio
import logging
import os
import time
import uuid
from pathlib import Path

from simulation_environment.simulation import CrowdSimulation, SimulationConfig
from server.observability.metrics import SIM_STEP, SIM_TIME, SIM_AGENTS, SIM_FPS, ML_FORECAST_ERROR, ML_FORECAST_ALERTS
from server.services.telemetry import TelemetryPublisher
from server.services.ml_service import MeasuredPredictor
from server.websocket import hub
from opentelemetry import trace

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("race.simulation")
ROOT = Path(__file__).resolve().parents[2]
SIM_ROOT = ROOT / "simulation_environment"

class SimulationRuntime:
    def __init__(self):
        config_path = SIM_ROOT / "config.json"
        self.config = SimulationConfig.from_json(config_path)
        self.ml_backend = os.getenv("RACE_ML_BACKEND", "pytorch").lower()
        if self.ml_backend == "onnx":
            # Avoid loading the PyTorch checkpoint when ONNX serving is selected.
            self.config.use_ml = False
        # Checkpoint paths in config are relative to simulation_environment.
        self.simulation = CrowdSimulation(config=self.config, project_root=SIM_ROOT)
        if self.ml_backend == "onnx":
            onnx_path = Path(os.getenv("RACE_ONNX_MODEL_PATH", str(SIM_ROOT / "ml" / "models" / "race_lstm.onnx")))
            if onnx_path.is_file():
                from simulation_environment.ml.onnx_inference import OnnxRACEPredictor
                self.simulation.ml.predictor = OnnxRACEPredictor(onnx_path)
                self.simulation.ml.enabled = True
            else:
                logger.warning("ONNX model not found at %s; ML disabled", onnx_path)
        if self.simulation.ml.enabled:
            self.simulation.ml.predictor = MeasuredPredictor(self.simulation.ml.predictor)
        self.lock = asyncio.Lock()
        self.session_id = str(uuid.uuid4())
        self.task = None
        self.stop_event = asyncio.Event()
        self.telemetry = TelemetryPublisher()
        self.last_error = None
        self.last_frame_wall_time = None
        self.frame_count_window = 0
        self.frame_window_started = time.perf_counter()
        self.forecast_alert_threshold = float(os.getenv("RACE_ML_ERROR_ALERT_UNITS", "2.0"))

    async def start(self):
        async with self.lock:
            if self.simulation.status != "completed":
                self.simulation.status = "running"
            if self.task is None or self.task.done():
                self.stop_event.clear()
                self.task = asyncio.create_task(self._run_loop(), name="race-simulation-loop")
            return self.frame()

    async def pause(self):
        async with self.lock:
            if self.simulation.status == "running":
                self.simulation.status = "paused"
            return self.frame()

    async def reset(self):
        async with self.lock:
            self.simulation.reset()
            self.session_id = str(uuid.uuid4())
            self.last_error = None
            return self.frame()

    async def snapshot(self):
        async with self.lock:
            return self.state()

    async def shutdown(self):
        self.stop_event.set()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        await self.telemetry.close()

    def state(self):
        return self.simulation.state()

    def environment_message(self):
        env = self.simulation.environment
        exits = []
        for exit_item in env.exits:
            half_w, half_h = 0.3, 1.25
            x0, x1 = max(0.0, exit_item.x-half_w), min(env.width, exit_item.x+half_w)
            y0, y1 = max(0.0, exit_item.y-half_h), min(env.height, exit_item.y+half_h)
            exits.append({"id": str(exit_item.id), "polygon": [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]})
        return {
            "type": "environment", "width": float(env.width), "height": float(env.height),
            "walls": [],
            "obstacles": [[[float(x), float(y)] for x,y in list(poly.exterior.coords)[:-1]] for poly in env.obstacles],
            "exits": exits,
        }

    def frame(self):
        state = self.state()
        agents = []
        for agent in state["agents"]:
            if agent["state"] == "evacuated":
                continue
            item = {"id": agent["id"], "x": agent["x"], "y": agent["y"],
                    "vx": agent["vx"], "vy": agent["vy"], "state": agent["state"]}
            predicted = agent.get("predicted_trajectory")
            if predicted:
                item["predicted"] = predicted
            agents.append(item)
        return {
            "type": "frame", "simulation_time": float(state["simulation_time"]),
            "total_agents": len(state["agents"]), "evacuated": int(state["evacuated_count"]),
            "density": float(state["density"]), "prediction_model": "lstm" if state["ml_enabled"] else "disabled",
            "agents": agents,
        }


    def _observe_forecast_error(self):
        """Compare each matured one-step forecast with the next sampled actual position."""
        if not self.simulation.ml.enabled:
            return
        interval = float(self.config.sample_interval_seconds)
        for agent in self.simulation.agents:
            prediction = agent.predicted_trajectory
            age = self.simulation.time - float(agent.last_prediction_at)
            if prediction is None or len(prediction) == 0 or age < interval - 1e-6:
                continue
            import numpy as np
            error = float(np.linalg.norm(np.asarray(prediction[0], dtype=np.float32) - agent.position))
            if np.isfinite(error):
                ML_FORECAST_ERROR.observe(error)
                if error > self.forecast_alert_threshold:
                    ML_FORECAST_ALERTS.inc()
            # Prevent counting the same matured forecast on subsequent ticks.
            agent.last_prediction_at = self.simulation.time

    async def _run_loop(self):
        tick = max(0.01, float(self.config.dt))
        deadline = time.perf_counter()
        while not self.stop_event.is_set():
            try:
                async with self.lock:
                    if self.simulation.status == "running":
                        started = time.perf_counter()
                        # Keep CPU-bound physics off the ASGI event loop.
                        self._observe_forecast_error()
                        with tracer.start_as_current_span("race.simulation.step") as span:
                            span.set_attribute("race.session_id", self.session_id)
                            span.set_attribute("race.active_agents", len(self.simulation.agents))
                            await asyncio.to_thread(self.simulation.step, 1)
                        elapsed = time.perf_counter() - started
                        SIM_STEP.observe(elapsed)
                        frame = self.frame()
                        SIM_TIME.set(frame["simulation_time"])
                        SIM_AGENTS.set(len(frame["agents"]))
                        self.frame_count_window += 1
                        now = time.perf_counter()
                        if now - self.frame_window_started >= 1:
                            SIM_FPS.set(self.frame_count_window / (now-self.frame_window_started))
                            self.frame_count_window = 0
                            self.frame_window_started = now
                        with tracer.start_as_current_span("race.telemetry.publish"):
                            await self.telemetry.publish(self.session_id, frame)
                        await hub.broadcast(frame)
                deadline += tick
                await asyncio.sleep(max(0.0, deadline-time.perf_counter()))
                if time.perf_counter() - deadline > tick * 4:
                    deadline = time.perf_counter()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.last_error = str(exc)
                logger.exception("Simulation loop failed")
                async with self.lock:
                    self.simulation.status = "paused"
                await asyncio.sleep(0.25)
