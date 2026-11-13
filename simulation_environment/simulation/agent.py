from collections import deque
from dataclasses import dataclass, field
import numpy as np

@dataclass
class PedestrianAgent:
    id: int
    position: np.ndarray
    goal_exit_id: str
    radius: float = 0.22
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.float64))
    state: str = "walking"
    trajectory_history: deque = field(default_factory=lambda: deque(maxlen=8))
    predicted_trajectory: np.ndarray | None = None
    evacuated_at: float | None = None
    last_prediction_at: float = -1e9
    navigation_path: list = field(default_factory=list)
    waypoint_index: int = 0

    def __post_init__(self):
        self.position = np.asarray(self.position, dtype=np.float64)
        self.velocity = np.asarray(self.velocity, dtype=np.float64)

    def record_position(self):
        self.trajectory_history.append(self.position.astype(np.float32).copy())

    def to_dict(self):
        return {
            "id": self.id,
            "x": float(self.position[0]),
            "y": float(self.position[1]),
            "vx": float(self.velocity[0]),
            "vy": float(self.velocity[1]),
            "radius": float(self.radius),
            "state": self.state,
            "goal_exit_id": self.goal_exit_id,
            "trajectory_history": [
                p.tolist() for p in self.trajectory_history
            ],
            "predicted_trajectory": (
                self.predicted_trajectory.tolist()
                if self.predicted_trajectory is not None
                else []
            )
        }
    