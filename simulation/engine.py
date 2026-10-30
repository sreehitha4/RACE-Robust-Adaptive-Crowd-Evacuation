"""Central Simulation Engine coordinating paths, movement, states, and metrics.

Manages execution ticks, dynamic rerouting upon environmental changes,
and clean separation of algorithmic simulation from Pygame visualization.
"""

from enum import Enum
from typing import List, Optional, Set, Tuple
from environment.building import Building
from environment.grid import CellType
from agents.agent import Agent, AgentState
from agents.manager import AgentManager
from algorithms.pathfinding import MultiSourceDistanceField, bfs_shortest_path
from simulation.movement import MovementResolver
from evaluation.metrics import EvacuationSummary, MetricsCollector


class SimulationState(Enum):
    """Execution state of the simulation engine."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class SimulationEngine:
    """Core simulation orchestrator."""

    def __init__(self, building: Building, agent_count: int = 20, seed: int = 42) -> None:
        self.building: Building = building
        self.agent_count: int = agent_count
        self.seed: int = seed

        self.manager: AgentManager = AgentManager(building)
        self.resolver: MovementResolver = MovementResolver(building, self.manager)
        self.metrics: MetricsCollector = MetricsCollector(self.manager)

        self.state: SimulationState = SimulationState.STOPPED
        self.current_tick: int = 0
        self.blocked_exits: Set[Tuple[int, int]] = set()

        # Initial spawn
        self.manager.spawn_agents(count=agent_count, seed=seed)
        self.recalculate_all_paths()

    def recalculate_all_paths(self) -> None:
        """Calculate or update the shortest paths for all active agents towards available exits."""
        # Find all currently unblocked exits
        active_exits = [
            e for e in self.building.grid.get_exits()
            if e not in self.blocked_exits and self.building.grid.is_walkable(e[0], e[1])
        ]

        if not active_exits:
            # If all exits are blocked, all active agents become stuck
            for agent in self.manager.active_agents:
                agent.mark_stuck(reason="All exits blocked")
            return

        # Compute optimal distance field
        field = MultiSourceDistanceField(self.building.grid, active_exits)

        for agent in self.manager.active_agents:
            path = field.get_path_from(agent.current_pos)
            if path is not None and len(path) > 0:
                agent.set_path(path, target_exit=path[-1])
            else:
                agent.mark_stuck(reason="No accessible exit found")

    def start(self) -> None:
        """Start the simulation execution."""
        if self.state in (SimulationState.STOPPED, SimulationState.PAUSED):
            if self.current_tick == 0:
                self.recalculate_all_paths()
            self.state = SimulationState.RUNNING

    def pause(self) -> None:
        """Pause the ongoing simulation."""
        if self.state == SimulationState.RUNNING:
            self.state = SimulationState.PAUSED

    def resume(self) -> None:
        """Resume a paused simulation."""
        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING

    def step(self) -> None:
        """Advance the simulation by exactly one discrete time tick."""
        if self.state != SimulationState.RUNNING:
            return

        self.current_tick += 1

        # Advance agents and resolve potential movement conflicts
        self.resolver.step(self.current_tick)

        # Check for completion: no more active agents
        if self.manager.is_evacuation_complete:
            self.state = SimulationState.COMPLETED

    def reset(self) -> None:
        """Reset simulation back to initial condition."""
        self.state = SimulationState.STOPPED
        self.current_tick = 0

        # Restore any blocked exits on the grid
        for bx, by in list(self.blocked_exits):
            self.building.grid.set_cell(bx, by, CellType.EXIT)
        self.blocked_exits.clear()

        # Reset agents to start positions and recalculate paths
        self.manager.reset_all()
        self.recalculate_all_paths()

    def restart_with_new_seed(self, new_seed: Optional[int] = None) -> None:
        """Respawn agents with a new random seed and reset."""
        if new_seed is not None:
            self.seed = new_seed
        else:
            self.seed += 1

        self.state = SimulationState.STOPPED
        self.current_tick = 0

        # Restore exits
        for bx, by in list(self.blocked_exits):
            self.building.grid.set_cell(bx, by, CellType.EXIT)
        self.blocked_exits.clear()

        self.manager.spawn_agents(count=self.agent_count, seed=self.seed)
        self.recalculate_all_paths()

    def toggle_exit_block(self, exit_coord: Tuple[int, int]) -> bool:
        """Dynamically block or unblock an emergency exit and trigger real-time rerouting.

        Returns:
            True if now blocked, False if unblocked.
        """
        ex, ey = exit_coord
        if not self.building.grid.is_inside(ex, ey):
            return False

        if exit_coord in self.blocked_exits:
            # Unblock
            self.blocked_exits.remove(exit_coord)
            self.building.grid.set_cell(ex, ey, CellType.EXIT)
            is_blocked = False
        else:
            # Block with wall
            self.blocked_exits.add(exit_coord)
            self.building.grid.set_cell(ex, ey, CellType.WALL)
            is_blocked = True

        # Reroute agents using new environment state
        self.recalculate_all_paths()
        return is_blocked

    def get_summary(self) -> EvacuationSummary:
        """Retrieve the current performance and metrics summary."""
        return self.metrics.get_summary(self.current_tick)
