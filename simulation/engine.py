"""Central Simulation Engine coordinating normal crowd flow and emergency egress.

Supports dual operating modes:
  1. NORMAL_FLOW: Everyday pedestrian dynamics, inter-room navigation, and natural circulation.
  2. EVACUATION: Emergency evacuation where all crowd members head to the nearest open exit.
"""

from enum import Enum
import random
from typing import Dict, List, Optional, Set, Tuple
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


class CrowdMode(Enum):
    """Operating crowd behavior mode."""
    NORMAL_FLOW = "NORMAL_FLOW"        # Everyday pedestrian circulation
    EVACUATION = "EVACUATION"          # Emergency evacuation to exits


class SimulationEngine:
    """Core simulation orchestrator supporting both normal pedestrian flow and evacuation."""

    def __init__(self, building: Building, agent_count: int = 20, seed: int = 42) -> None:
        self.building: Building = building
        self.agent_count: int = agent_count
        self.seed: int = seed

        self.manager: AgentManager = AgentManager(building)
        self.resolver: MovementResolver = MovementResolver(building, self.manager)
        self.metrics: MetricsCollector = MetricsCollector(self.manager)

        self.state: SimulationState = SimulationState.STOPPED
        self.crowd_mode: CrowdMode = CrowdMode.NORMAL_FLOW  # Default to normal crowd behavior!
        self.current_tick: int = 0
        self.blocked_exits: Set[Tuple[int, int]] = set()

        # Initial spawn
        self.manager.spawn_agents(count=agent_count, seed=seed)
        self.setup_agent_routes()

    def set_mode(self, mode: CrowdMode) -> None:
        """Switch between Normal Everyday Crowd Flow and Emergency Evacuation."""
        self.crowd_mode = mode
        if mode == CrowdMode.EVACUATION:
            # Re-plan all agents to nearest open exit
            self.recalculate_evacuation_paths()
        else:
            # Re-plan normal crowd navigation targets
            self.assign_normal_crowd_destinations()

    def setup_agent_routes(self) -> None:
        """Initialize routes based on active crowd mode."""
        if self.crowd_mode == CrowdMode.EVACUATION:
            self.recalculate_evacuation_paths()
        else:
            self.assign_normal_crowd_destinations()

    def assign_normal_crowd_destinations(self) -> None:
        """Assign diverse everyday destinations (rooms, concourse, main doors) for natural crowd flow."""
        grid = self.building.grid
        rng = random.Random(self.seed + self.current_tick)

        # Collect candidate destinations from rooms and major doors
        destination_pools: List[Tuple[int, int]] = []
        for room in self.building.rooms.values():
            destination_pools.extend(room.get_interior_cells())
        destination_pools.extend(self.building.exits)

        walkable_pools = [pos for pos in destination_pools if grid.is_walkable(pos[0], pos[1])]

        for agent in self.manager.agents:
            if not agent.is_active and not agent.is_evacuated:
                continue

            # Pick a realistic room or concourse destination different from current position
            target = rng.choice(walkable_pools)
            path = bfs_shortest_path(grid, start=agent.current_pos, goals=[target])
            if path and len(path) > 1:
                agent.set_path(path, target_exit=target)
                agent.normal_target = target
                if agent.state == AgentState.EVACUATED:
                    agent.state = AgentState.ACTIVE

    def recalculate_evacuation_paths(self) -> None:
        """Calculate optimal BFS paths for all active agents towards available emergency exits."""
        active_exits = [
            e for e in self.building.grid.get_exits()
            if e not in self.blocked_exits and self.building.grid.is_walkable(e[0], e[1])
        ]

        if not active_exits:
            for agent in self.manager.active_agents:
                agent.mark_stuck(reason="All exits blocked")
            return

        field = MultiSourceDistanceField(self.building.grid, active_exits)

        for agent in self.manager.active_agents:
            path = field.get_path_from(agent.current_pos)
            if path is not None and len(path) > 0:
                agent.set_path(path, target_exit=path[-1])
            else:
                agent.mark_stuck(reason="No accessible exit found")

    def recalculate_all_paths(self) -> None:
        """Polymorphic router update based on active mode."""
        self.setup_agent_routes()

    def start(self) -> None:
        """Start simulation."""
        if self.state in (SimulationState.STOPPED, SimulationState.PAUSED):
            if self.current_tick == 0:
                self.setup_agent_routes()
            self.state = SimulationState.RUNNING

    def pause(self) -> None:
        """Pause simulation."""
        if self.state == SimulationState.RUNNING:
            self.state = SimulationState.PAUSED

    def resume(self) -> None:
        """Resume simulation."""
        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING

    def step(self) -> None:
        """Execute one discrete time tick."""
        if self.state != SimulationState.RUNNING:
            return

        self.current_tick += 1

        # Move agents
        self.resolver.step(self.current_tick)

        # In NORMAL_FLOW: When an agent reaches their room destination or exit,
        # assign them a new activity / destination so the crowd circulates naturally!
        if self.crowd_mode == CrowdMode.NORMAL_FLOW:
            grid = self.building.grid
            rng = random.Random(self.seed + self.current_tick * 7)
            # Find agents who reached their destination or evacuated
            for agent in self.manager.agents:
                if agent.is_evacuated or (agent.is_active and agent.next_intended_cell is None):
                    # Agent reached destination: choose new destination to simulate continuous walking
                    candidates = []
                    for room in self.building.rooms.values():
                        candidates.extend(room.get_interior_cells())
                    walkable = [c for c in candidates if grid.is_walkable(c[0], c[1])]
                    new_target = rng.choice(walkable)
                    path = bfs_shortest_path(grid, agent.current_pos, [new_target])
                    if path and len(path) > 1:
                        agent.set_path(path, target_exit=new_target)
                        agent.normal_target = new_target
                        agent.state = AgentState.ACTIVE

        # In EVACUATION mode: check completion when everyone evacuated or stuck
        elif self.crowd_mode == CrowdMode.EVACUATION:
            if self.manager.is_evacuation_complete:
                self.state = SimulationState.COMPLETED

    def reset(self) -> None:
        """Reset simulation back to initial condition."""
        self.state = SimulationState.STOPPED
        self.current_tick = 0

        # Restore any blocked exits
        for bx, by in list(self.blocked_exits):
            self.building.grid.set_cell(bx, by, CellType.EXIT)
        self.blocked_exits.clear()

        # Reset agents to start positions and recalculate paths
        self.manager.reset_all()
        self.setup_agent_routes()

    def restart_with_new_seed(self, new_seed: Optional[int] = None) -> None:
        """Respawn agents with a new random seed."""
        if new_seed is not None:
            self.seed = new_seed
        else:
            self.seed += 1

        self.state = SimulationState.STOPPED
        self.current_tick = 0

        for bx, by in list(self.blocked_exits):
            self.building.grid.set_cell(bx, by, CellType.EXIT)
        self.blocked_exits.clear()

        self.manager.spawn_agents(count=self.agent_count, seed=self.seed)
        self.setup_agent_routes()

    def toggle_exit_block(self, exit_coord: Tuple[int, int]) -> bool:
        """Dynamically block/unblock an exit."""
        ex, ey = exit_coord
        if not self.building.grid.is_inside(ex, ey):
            return False

        if exit_coord in self.blocked_exits:
            self.blocked_exits.remove(exit_coord)
            self.building.grid.set_cell(ex, ey, CellType.EXIT)
            is_blocked = False
        else:
            self.blocked_exits.add(exit_coord)
            self.building.grid.set_cell(ex, ey, CellType.WALL)
            is_blocked = True

        self.setup_agent_routes()
        return is_blocked

    def get_summary(self) -> EvacuationSummary:
        """Retrieve metrics summary."""
        return self.metrics.get_summary(self.current_tick)
