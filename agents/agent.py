"""Agent entity representation and lifecycle states.

Encapsulates individual crowd agent properties, current state,
assigned path, progress tracking, and evacuation statistics.
"""

from enum import Enum
from typing import List, Optional, Tuple


class AgentState(Enum):
    """Lifecycle state of a simulation agent."""
    ACTIVE = "ACTIVE"
    EVACUATED = "EVACUATED"
    STUCK = "STUCK"


class Agent:
    """Represents a discrete person in the crowd evacuation simulation."""

    def __init__(self, agent_id: int, start_pos: Tuple[int, int]) -> None:
        """Initialize an agent.

        Args:
            agent_id: Unique integer identifier.
            start_pos: Starting (x, y) grid coordinates.
        """
        self.agent_id: int = agent_id
        self.start_pos: Tuple[int, int] = start_pos
        self.current_pos: Tuple[int, int] = start_pos

        self.state: AgentState = AgentState.ACTIVE
        self.target_exit: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
        self.path_index: int = 0

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
        """Check if agent has successfully exited."""
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
        """Assign a newly calculated path and optional target exit to the agent."""
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
        """Record a tick where the agent had to wait due to congestion or blockage."""
        self.wait_ticks += 1

    def mark_evacuated(self, current_tick: int) -> None:
        """Transition agent state to EVACUATED upon reaching an exit."""
        self.state = AgentState.EVACUATED
        self.evacuation_tick = current_tick

    def mark_stuck(self, reason: str = "No path to exit") -> None:
        """Transition agent state to STUCK."""
        self.state = AgentState.STUCK
        self.stuck_reason = reason

    def reset(self) -> None:
        """Reset agent back to original initial condition."""
        self.current_pos = self.start_pos
        self.state = AgentState.ACTIVE
        self.path_index = 0
        self.steps_taken = 0
        self.wait_ticks = 0
        self.evacuation_tick = None
        self.stuck_reason = None

    def __repr__(self) -> str:
        return f"Agent(id={self.agent_id}, pos={self.current_pos}, state={self.state.value})"
