"""Continuous 2D Agent Entity with Social Dynamics and Helbing Physics.

Encapsulates individual physical properties (continuous position, velocity, mass),
social group bonds (pairs, companions), panic/stress states, and personal dossier.
"""

from enum import Enum
import math
from typing import List, Optional, Tuple
from simulation.physics import Vector2


class AgentState(Enum):
    """Lifecycle state of an agent."""
    ACTIVE = "ACTIVE"
    EVACUATED = "EVACUATED"
    STUCK = "STUCK"


class PanicLevel(Enum):
    """Psychological alertness state."""
    CALM = "CALM"          # Normal walking, polite personal spacing (1.2 m/s)
    ALERT = "ALERT"        # Quickened pace, looking for exits (1.8 m/s)
    PANIC = "PANIC"        # High urgency, pushing at bottlenecks (2.6 m/s)


FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Casey", "Riley",
    "Avery", "Logan", "Dakota", "Reese", "Quinn", "Skyler", "Cameron", "Jesse",
    "Pat", "Rowan", "Hayden", "Finley", "Emerson", "Adrian", "Kai", "Sloan"
]


class Agent:
    """Represents a discrete person in continuous 2D space."""

    def __init__(
        self,
        agent_id: int,
        start_pos: Tuple[float, float],
        group_id: Optional[int] = None,
        name: Optional[str] = None
    ) -> None:
        self.agent_id: int = agent_id
        self.name: str = name or FIRST_NAMES[(agent_id - 1) % len(FIRST_NAMES)]

        # Continuous physical coordinates
        self.pos: Vector2 = Vector2(float(start_pos[0]), float(start_pos[1]))
        self.vel: Vector2 = Vector2(0.0, 0.0)
        self.start_pos: Tuple[int, int] = (int(start_pos[0]), int(start_pos[1]))
        self.current_pos: Tuple[int, int] = self.start_pos  # Discrete grid cell sync

        # Physical dimensions
        self.radius: float = 0.38      # Body radius
        self.mass: float = 70.0        # Mass in kg

        # Social & Psychological Attributes
        self.group_id: Optional[int] = group_id
        self.companion_id: Optional[int] = None
        self.panic_level: PanicLevel = PanicLevel.CALM
        self.stress_level: float = 0.1   # Range 0.0 to 1.0

        # Speeds in units/sec
        self.base_calm_speed: float = 1.2
        self.base_panic_speed: float = 2.6
        self.speed_factor: float = 1.0

        # Navigation & Route
        self.state: AgentState = AgentState.ACTIVE
        self.path: List[Tuple[int, int]] = []
        self.path_index: int = 0
        self.target_exit: Optional[Tuple[int, int]] = None
        self.normal_target: Optional[Tuple[int, int]] = None

        # Position Trail History (for smooth visual trajectory ribbon)
        self.trail: List[Tuple[float, float]] = []
        self.max_trail_len: int = 8

        # Metrics & Congestion Rerouting
        self.rerouted: bool = False
        self.steps_taken: int = 0
        self.wait_ticks: int = 0
        self.evacuation_tick: Optional[int] = None
        self.stuck_reason: Optional[str] = None

    @property
    def desired_speed(self) -> float:
        """Dynamic desired walking speed based on panic/stress state."""
        if self.panic_level == PanicLevel.PANIC:
            base = self.base_panic_speed
        elif self.panic_level == PanicLevel.ALERT:
            base = (self.base_calm_speed + self.base_panic_speed) * 0.5
        else:
            base = self.base_calm_speed
        return base * self.speed_factor

    @property
    def is_active(self) -> bool:
        return self.state == AgentState.ACTIVE

    @property
    def is_evacuated(self) -> bool:
        return self.state == AgentState.EVACUATED

    @property
    def is_stuck(self) -> bool:
        return self.state == AgentState.STUCK

    @property
    def visual_x(self) -> float:
        return self.pos.x

    @property
    def visual_y(self) -> float:
        return self.pos.y

    @property
    def next_intended_cell(self) -> Optional[Tuple[int, int]]:
        """Next discrete waypoint along path."""
        if not self.is_active or not self.path:
            return None
        next_idx = self.path_index + 1
        if next_idx < len(self.path):
            return self.path[next_idx]
        return None

    def set_path(self, path: List[Tuple[int, int]], target_exit: Optional[Tuple[int, int]] = None) -> None:
        """Assign a calculated global path."""
        self.path = list(path)
        self.path_index = 0
        self.target_exit = target_exit
        self.stuck_reason = None
        if self.state == AgentState.STUCK:
            self.state = AgentState.ACTIVE

    def advance_to(self, new_pos: Tuple[int, int]) -> None:
        """Advance discrete path index."""
        self.current_pos = new_pos
        self.path_index += 1
        self.steps_taken += 1

    def record_wait(self) -> None:
        self.wait_ticks += 1
        # Waiting in crowd bottlenecks increases stress!
        self.stress_level = min(1.0, self.stress_level + 0.05)

    def mark_evacuated(self, current_tick: int) -> None:
        self.state = AgentState.EVACUATED
        self.evacuation_tick = current_tick
        self.stress_level = 0.0

    def mark_stuck(self, reason: str = "Blocked") -> None:
        self.state = AgentState.STUCK
        self.stuck_reason = reason
        self.stress_level = 1.0

    def integrate_physics(self, force: Vector2, dt: float, max_speed: float = 3.5) -> None:
        """Euler numerical integration of acceleration, velocity, and continuous position."""
        accel = force / self.mass
        self.vel = self.vel + accel * dt

        # Cap terminal velocity
        speed = self.vel.length()
        if speed > max_speed:
            self.vel = (self.vel / speed) * max_speed

        self.pos = self.pos + self.vel * dt
        self.current_pos = (int(round(self.pos.x)), int(round(self.pos.y)))

        # Update trail history
        if not self.trail or (abs(self.trail[-1][0] - self.pos.x) + abs(self.trail[-1][1] - self.pos.y)) > 0.2:
            self.trail.append((self.pos.x, self.pos.y))
            if len(self.trail) > self.max_trail_len:
                self.trail.pop(0)

    def reset(self) -> None:
        """Reset agent to initial start condition."""
        self.pos = Vector2(float(self.start_pos[0]), float(self.start_pos[1]))
        self.vel = Vector2(0.0, 0.0)
        self.current_pos = self.start_pos
        self.state = AgentState.ACTIVE
        self.path_index = 0
        self.steps_taken = 0
        self.wait_ticks = 0
        self.evacuation_tick = None
        self.stuck_reason = None
        self.stress_level = 0.1
        self.trail.clear()

    def update_visual(self, lerp_speed: float = 0.25) -> None:
        """Compatibility hook."""
        pass

    def __repr__(self) -> str:
        return f"Agent({self.name} #{self.agent_id}, pos=({self.pos.x:.1f}, {self.pos.y:.1f}), {self.state.value})"
