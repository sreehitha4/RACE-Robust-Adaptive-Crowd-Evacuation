from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class SimulationConfig:
    room_width: float = 20.0
    room_height: float = 14.0
    dt: float = 0.1
    sample_interval_seconds: float = 0.4
    agent_count: int = 24
    agent_radius: float = 0.22
    preferred_speed: float = 1.15
    max_speed: float = 1.6
    goal_weight: float = 0.72
    prediction_weight: float = 0.28
    separation_weight: float = 1.15
    separation_distance: float = 0.75
    obstacle_clearance: float = 0.12
    exit_radius: float = 0.55
    max_simulation_seconds: float = 180.0
    random_seed: int = 42
    use_ml: bool = True
    checkpoint_path: str = "ml/models/trajectory_lstm_best.pth"
    prediction_refresh_seconds: float = 0.4

    @classmethod
    def from_json(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in allowed})

    def validate(self):
        if self.room_width <= 2 or self.room_height <= 2:
            raise ValueError("Room dimensions must both be greater than 2.")
        if self.dt <= 0 or self.sample_interval_seconds <= 0:
            raise ValueError("Time intervals must be positive.")
        if self.agent_count < 1 or self.agent_radius <= 0:
            raise ValueError("Agent count and radius must be positive.")
        if abs(self.goal_weight + self.prediction_weight - 1.0) > 1e-6:
            raise ValueError("goal_weight + prediction_weight must equal 1.0")
