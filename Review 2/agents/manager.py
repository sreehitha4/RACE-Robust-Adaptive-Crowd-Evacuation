"""Agent Manager for continuous crowd spawning, group pairing, and interactive queries.

Manages social group clustering, interactive mouse spawning,
and population-level panic state modulation.
"""

import random
from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building
from environment.grid import CellType
from simulation.physics import Vector2
from .agent import Agent, AgentState, PanicLevel


class AgentManager:
    """Manages continuous crowd agents, social groups, and interactive inspector lookups."""

    def __init__(self, building: Building) -> None:
        self.building: Building = building
        self.agents: List[Agent] = []
        self._agents_by_id: Dict[int, Agent] = {}
        self.selected_agent: Optional[Agent] = None

    @property
    def total_count(self) -> int:
        return len(self.agents)

    @property
    def active_agents(self) -> List[Agent]:
        return [a for a in self.agents if a.is_active]

    @property
    def evacuated_agents(self) -> List[Agent]:
        return [a for a in self.agents if a.is_evacuated]

    @property
    def stuck_agents(self) -> List[Agent]:
        return [a for a in self.agents if a.is_stuck]

    @property
    def is_evacuation_complete(self) -> bool:
        return len(self.active_agents) == 0

    def get_agent(self, agent_id: int) -> Optional[Agent]:
        return self._agents_by_id.get(agent_id)

    def add_agent(self, agent: Agent) -> None:
        self.agents.append(agent)
        self._agents_by_id[agent.agent_id] = agent

    def clear(self) -> None:
        self.agents.clear()
        self._agents_by_id.clear()
        self.selected_agent = None

    def spawn_agents(
        self,
        count: int = 25,
        seed: Optional[int] = 42,
        group_pair_ratio: float = 0.4
    ) -> List[Agent]:
        """Spawn crowd agents with realistic social group pairing."""
        self.clear()
        rng = random.Random(seed)
        grid = self.building.grid

        # Collect candidate floor cells
        candidates: List[Tuple[int, int]] = []
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.get_cell(x, y) == CellType.FLOOR:
                    candidates.append((x, y))

        if len(candidates) < count:
            raise ValueError(f"Requested {count} agents, but only {len(candidates)} walkable floor cells exist.")

        rng.shuffle(candidates)
        chosen_positions = candidates[:count]

        group_counter = 1
        i = 0
        while i < count:
            pos1 = chosen_positions[i]
            speed1 = round(rng.uniform(0.88, 1.18), 2)

            # Determine if this person walks with a companion
            is_pair = (i + 1 < count) and (rng.random() < group_pair_ratio)

            if is_pair:
                gid = group_counter
                group_counter += 1
                pos2 = chosen_positions[i + 1]
                speed2 = round(rng.uniform(0.88, 1.18), 2)

                a1 = Agent(agent_id=i + 1, start_pos=(pos1[0] + 0.5, pos1[1] + 0.5), group_id=gid)
                a2 = Agent(agent_id=i + 2, start_pos=(pos2[0] + 0.5, pos2[1] + 0.5), group_id=gid)

                a1.speed_factor = speed1
                a2.speed_factor = speed2
                a1.companion_id = a2.agent_id
                a2.companion_id = a1.agent_id

                self.agents.extend([a1, a2])
                self._agents_by_id[a1.agent_id] = a1
                self._agents_by_id[a2.agent_id] = a2
                i += 2
            else:
                agent = Agent(agent_id=i + 1, start_pos=(pos1[0] + 0.5, pos1[1] + 0.5), group_id=None)
                agent.speed_factor = speed1
                self.agents.append(agent)
                self._agents_by_id[agent.agent_id] = agent
                i += 1

        return self.agents

    def spawn_single_at(self, x: float, y: float) -> Optional[Agent]:
        """Interactively spawn an agent at mouse coordinates."""
        gx, gy = int(x), int(y)
        if not self.building.grid.is_walkable(gx, gy):
            return None

        new_id = len(self.agents) + 1
        agent = Agent(agent_id=new_id, start_pos=(x, y))
        self.agents.append(agent)
        self._agents_by_id[new_id] = agent
        return agent

    def find_agent_near(self, gx: float, gy: float, max_dist: float = 0.8) -> Optional[Agent]:
        """Find the closest agent within max_dist radius of continuous coordinate."""
        closest: Optional[Agent] = None
        min_d = max_dist

        for agent in self.active_agents:
            d = math.hypot(agent.pos.x - gx, agent.pos.y - gy)
            if d < min_d:
                min_d = d
                closest = agent

        return closest

    def set_panic_level(self, level: PanicLevel) -> None:
        """Set uniform panic level across crowd."""
        for agent in self.agents:
            agent.panic_level = level
            if level == PanicLevel.PANIC:
                agent.stress_level = min(1.0, agent.stress_level + 0.6)
            elif level == PanicLevel.CALM:
                agent.stress_level = 0.1

    def reset_all(self) -> None:
        """Reset all agents back to start positions."""
        for agent in self.agents:
            agent.reset()
        self.selected_agent = None

    def get_occupied_cells(self) -> Set[Tuple[int, int]]:
        return {agent.current_pos for agent in self.active_agents}
