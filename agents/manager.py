"""Agent Manager for crowd spawning, population tracking, and state queries.

Ensures deterministic, valid agent placement without collisions,
and manages population-level lifecycle updates.
"""

import random
from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building
from environment.grid import CellType
from .agent import Agent, AgentState


class AgentManager:
    """Manages the lifecycle, placement, and population status of all crowd agents."""

    def __init__(self, building: Building) -> None:
        self.building: Building = building
        self.agents: List[Agent] = []
        self._agents_by_id: Dict[int, Agent] = {}

    @property
    def total_count(self) -> int:
        """Total number of registered agents."""
        return len(self.agents)

    @property
    def active_agents(self) -> List[Agent]:
        """List of agents currently actively evacuating."""
        return [a for a in self.agents if a.is_active]

    @property
    def evacuated_agents(self) -> List[Agent]:
        """List of agents that have successfully reached an exit."""
        return [a for a in self.agents if a.is_evacuated]

    @property
    def stuck_agents(self) -> List[Agent]:
        """List of agents marked as stuck."""
        return [a for a in self.agents if a.is_stuck]

    @property
    def is_evacuation_complete(self) -> bool:
        """True if every agent has either evacuated or become stuck (no active agents)."""
        return len(self.active_agents) == 0

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Retrieve an agent by its unique identifier."""
        return self._agents_by_id.get(agent_id)

    def clear(self) -> None:
        """Clear all registered agents."""
        self.agents.clear()
        self._agents_by_id.clear()

    def spawn_agents(self, count: int = 20, seed: Optional[int] = 42) -> List[Agent]:
        """Spawn a population of agents distributed across valid building rooms and corridors.

        Guarantees:
          - No agent spawns in a wall.
          - No agent spawns outside grid bounds.
          - No two agents share the same starting cell.
          - No agent spawns directly on an emergency exit.

        Args:
            count: Number of agents to spawn.
            seed: Reproducible pseudo-random seed.

        Returns:
            List of successfully instantiated agents.
        """
        self.clear()
        rng = random.Random(seed)

        # Collect all valid walkable candidate cells that are NOT exits
        grid = self.building.grid
        candidates: List[Tuple[int, int]] = []

        for y in range(grid.height):
            for x in range(grid.width):
                if grid.get_cell(x, y) == CellType.FLOOR:
                    candidates.append((x, y))

        if len(candidates) < count:
            raise ValueError(
                f"Requested {count} agents, but only {len(candidates)} walkable floor cells exist."
            )

        # Shuffle candidates deterministically
        rng.shuffle(candidates)
        chosen_positions = candidates[:count]

        for i, pos in enumerate(chosen_positions):
            agent = Agent(agent_id=i + 1, start_pos=pos)
            self.agents.append(agent)
            self._agents_by_id[agent.agent_id] = agent

        return self.agents

    def reset_all(self) -> None:
        """Reset all agents back to their starting positions and active states."""
        for agent in self.agents:
            agent.reset()

    def get_occupied_cells(self) -> Set[Tuple[int, int]]:
        """Return the set of all current coordinates occupied by active agents."""
        return {agent.current_pos for agent in self.active_agents}
