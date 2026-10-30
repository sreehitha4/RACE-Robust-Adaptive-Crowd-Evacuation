"""Agent entity representation with normal crowd behavior and smooth visual physics.

Encapsulates individual pedestrian traits, natural walking speeds,
continuous position interpolation, lifecycle states, and route tracking.
"""

from enum import Enum
import random
from typing import List, Optional, Tuple


class AgentState(Enum):
    """Lifecycle state of an agent."""
    ACTIVE = "ACTIVE"
    EVACUATED = "EVACUATED"
    STUCK = "STUCK"


class Agent:
    """Represents a person with natural crowd behavior and smooth visual rendering."""

    def __init__(self, agent_id: int, start_pos: Tuple[int, int], speed_factor: float = 1.0) -> None:
        self.agent_id: int = agent_id
        self.start_pos: Tuple[int, int] = start_pos
        self.current_pos: Tuple[int, int] = start_pos

        # Smooth visual position in pixel coordinates
        self.visual_x: float = float(start_pos[0])
        self.visual_y: float = float(start_pos[1])

        # Natural crowd attributes
        self.speed_factor: float = speed_factor
        self.state: AgentState = AgentState.ACTIVE
        self.target_exit: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
        self.path_index: int = 0

        # Normal crowd target destination (when not in emergency evacuation)
        self.normal_target: Optional[Tuple[int, int]] = None

        # Performance & movement metrics
        self.steps_taken: int = 0
        self.wait_ticks: int = 0
        self.evacuation_tick: Optional[int] = None
        self.stuck_reason: Optional[str] = None

    @property
    def is_active(self) -> bool:
        """Check if agent is still actively navigating the building."""
        return self.state == AgentState.ACTIVE

    @property
    def is_evacuated(self) -> bool:
        """Check if agent has reached an exit."""
        return self.state == AgentState.EVACUATED

    @property
    def is_stuck(self) -> bool:
        """Check if agent is trapped or blocked."""
        return self.state == AgentState.STUCK

    @property
    def next_intended_cell(self) -> Optional[Tuple[int, int]]:
        """Peek at the next cell along the calculated path."""
        if not self.is_active or not self.path:
            return None
        next_idx = self.path_index + 1
        if next_idx < len(self.path):
            return self.path[next_idx]
        return None

    def set_path(self, path: List[Tuple[int, int]], target_exit: Optional[Tuple[int, int]] = None) -> None:
        """Assign a calculated path and target destination."""
        self.path = list(path)
        self.path_index = 0
        self.target_exit = target_exit
        self.stuck_reason = None
        if self.state == AgentState.STUCK:
            self.state = AgentState.ACTIVE

    def advance_to(self, new_pos: Tuple[int, int]) -> None:
        """Advance agent to new coordinate and increment path progress."""
        self.current_pos = new_pos
        self.path_index += 1
        self.steps_taken += 1

    def record_wait(self) -> None:
        """Record a tick where the agent waited due to crowd congestion."""
        self.wait_ticks += 1

    def mark_evacuated(self, current_tick: int) -> None:
        """Transition agent state to EVACUATED upon reaching an exit."""
        self.state = AgentState.EVACUATED
        self.evacuation_tick = current_tick

    def mark_stuck(self, reason: str = "No reachable path") -> None:
        """Transition agent state to STUCK."""
        self.state = AgentState.STUCK
        self.stuck_reason = reason

    def update_visual(self, lerp_speed: float = 0.25) -> None:
        """Smoothly interpolate visual coordinates towards current grid position.

        Provides fluid visual movement rather than jarring cell jumping.
        """
        target_gx, target_gy = self.current_pos
        self.visual_x += (target_gx - self.visual_x) * lerp_speed
        self.visual_y += (target_gy - self.visual_y) * lerp_speed

    def reset(self) -> None:
        """Reset agent back to original initial condition."""
        self.current_pos = self.start_pos
        self.visual_x = float(self.start_pos[0])
        self.visual_y = float(self.start_pos[1])
        self.state = AgentState.ACTIVE
        self.path_index = 0
        self.steps_taken = 0
        self.wait_ticks = 0
        self.evacuation_tick = None
        self.stuck_reason = None

    def __repr__(self) -> str:
        return f"Agent(id={self.agent_id}, pos={self.current_pos}, state={self.state.value})"
