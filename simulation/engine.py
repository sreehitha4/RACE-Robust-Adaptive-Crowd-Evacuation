"""Central Simulation Engine with Continuous Social Force Physics and Interactivity.

Coordinates:
  - Dual modes (Normal Pedestrian Flow vs Emergency Evacuation).
  - Helbing Social Force Model continuous crowd updates.
  - Congestion-Aware Dynamic Exit Balancing (diverting crowd from jammed exits to open ones).
  - Multiple Unseen Architectural Floor Plans (Campus, Office Suites, Airport Terminal, Procedural).
  - Interactive hazard placement (fire/barriers) and live BFS re-routing.
  - Mouse-driven agent spawning and occupant inspection.
  - Dynamic panic levels (Calm, Alert, Panic).
"""

from enum import Enum
import random
from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building
from environment.grid import CellType
from simulation.physics import Vector2
from agents.agent import Agent, AgentState, PanicLevel
from agents.manager import AgentManager
from algorithms.pathfinding import MultiSourceDistanceField, bfs_shortest_path
from simulation.movement import MovementResolver
from evaluation.metrics import EvacuationSummary, MetricsCollector


class SimulationState(Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class CrowdMode(Enum):
    NORMAL_FLOW = "NORMAL_FLOW"
    EVACUATION = "EVACUATION"


class SimulationEngine:
    """Orchestrates continuous crowd physics, congestion-aware routing, and interactive events."""

    def __init__(self, building: Building, agent_count: int = 25, seed: int = 42) -> None:
        self.building: Building = building
        self.agent_count: int = agent_count
        self.seed: int = seed

        self.manager: AgentManager = AgentManager(building)
        self.resolver: MovementResolver = MovementResolver(building, self.manager)
        self.metrics: MetricsCollector = MetricsCollector(self.manager)

        self.state: SimulationState = SimulationState.STOPPED
        self.crowd_mode: CrowdMode = CrowdMode.NORMAL_FLOW
        self.current_tick: int = 0
        self.blocked_exits: Set[Tuple[int, int]] = set()

        # Congestion-Aware Dynamic Egress Rerouting
        self.congestion_reroute_enabled: bool = True
        self.rerouted_count: int = 0
        self.exit_queues: Dict[Tuple[int, int], int] = {}

        # Initial spawn with social group pairs
        self.manager.spawn_agents(count=agent_count, seed=seed)
        self.setup_agent_routes()

    def set_mode(self, mode: CrowdMode) -> None:
        """Switch between Normal Everyday Crowd Flow and Emergency Evacuation."""
        self.crowd_mode = mode
        if mode == CrowdMode.EVACUATION:
            self.manager.set_panic_level(PanicLevel.ALERT)
            self.recalculate_evacuation_paths()
        else:
            self.manager.set_panic_level(PanicLevel.CALM)
            self.assign_normal_crowd_destinations()

    def set_panic(self, level: PanicLevel) -> None:
        """Modulate crowd psychological urgency."""
        self.manager.set_panic_level(level)

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

        destination_pools: List[Tuple[int, int]] = []
        for room in self.building.rooms.values():
            destination_pools.extend(room.get_interior_cells())
        destination_pools.extend(self.building.exits)

        walkable_pools = [pos for pos in destination_pools if grid.is_walkable(pos[0], pos[1])]

        for agent in self.manager.agents:
            if not agent.is_active and not agent.is_evacuated:
                continue

            target = rng.choice(walkable_pools)
            path = bfs_shortest_path(grid, start=agent.current_pos, goals=[target])
            if path and len(path) > 1:
                agent.set_path(path, target_exit=target)
                agent.normal_target = target
                if agent.state == AgentState.EVACUATED:
                    agent.state = AgentState.ACTIVE

    def recalculate_evacuation_paths(self) -> None:
        """Calculate optimal BFS paths towards available emergency exits."""
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

    def check_congestion_rerouting(self) -> None:
        """Detect exit congestion bottlenecks and dynamically reroute trailing crowd members
        to less congested nearby exits.
        """
        if not self.congestion_reroute_enabled or self.crowd_mode != CrowdMode.EVACUATION:
            return

        active_agents = self.manager.active_agents
        if not active_agents:
            return

        # 1. Group individual exit cells into distinct exit portals
        active_exits = [
            e for e in self.building.grid.get_exits()
            if e not in self.blocked_exits and self.building.grid.is_walkable(e[0], e[1])
        ]
        if len(active_exits) <= 1:
            return

        portals: List[List[Tuple[int, int]]] = []
        for e in active_exits:
            matched = False
            for p in portals:
                if any(abs(e[0] - pe[0]) + abs(e[1] - pe[1]) <= 2 for pe in p):
                    p.append(e)
                    matched = True
                    break
            if not matched:
                portals.append([e])

        # 2. Count crowd queue at each portal (agents targeting or within 4.5m)
        portal_queues: Dict[int, int] = {idx: 0 for idx in range(len(portals))}
        for agent in active_agents:
            for p_idx, portal in enumerate(portals):
                is_targeting = agent.target_exit in portal
                near_portal = any(agent.pos.distance_to(Vector2(pe[0] + 0.5, pe[1] + 0.5)) < 4.5 for pe in portal)
                if is_targeting or near_portal:
                    portal_queues[p_idx] += 1

        self.exit_queues = {tuple(p[0]): portal_queues[idx] for idx, p in enumerate(portals)}

        # 3. Trailing agents evaluate if alternative exits are faster
        grid = self.building.grid
        for agent in active_agents:
            cur_target = agent.target_exit
            if not cur_target:
                continue

            cur_p_idx = next((idx for idx, p in enumerate(portals) if cur_target in p), None)
            if cur_p_idx is None:
                continue

            cur_queue = portal_queues[cur_p_idx]
            if cur_queue < 3:
                continue  # No significant bottleneck at this exit

            dist_to_cur = agent.pos.distance_to(Vector2(cur_target[0] + 0.5, cur_target[1] + 0.5))
            if dist_to_cur < 3.2:
                continue  # Already close to portal, do not turn back

            cost_cur = dist_to_cur + (cur_queue * 1.5)

            # Evaluate alternative portals
            best_alt_portal = None
            best_alt_cost = cost_cur
            best_alt_path = None

            for alt_idx, alt_p in enumerate(portals):
                if alt_idx == cur_p_idx:
                    continue
                alt_queue = portal_queues[alt_idx]
                alt_target = alt_p[0]
                dist_to_alt = agent.pos.distance_to(Vector2(alt_target[0] + 0.5, alt_target[1] + 0.5))
                cost_alt = dist_to_alt + (alt_queue * 1.5)

                # Must be substantially better (by at least 3.5 units) to prevent oscillation
                if cost_alt + 3.5 < best_alt_cost:
                    path = bfs_shortest_path(grid, agent.current_pos, alt_p)
                    if path and len(path) > 1:
                        best_alt_cost = cost_alt
                        best_alt_portal = alt_p
                        best_alt_path = path

            if best_alt_path and best_alt_portal:
                agent.set_path(best_alt_path, target_exit=best_alt_path[-1])
                agent.rerouted = True
                self.rerouted_count += 1
                portal_queues[cur_p_idx] -= 1
                new_idx = next(idx for idx, p in enumerate(portals) if p == best_alt_portal)
                portal_queues[new_idx] += 1

    def load_floor_plan(self, plan_type: str) -> None:
        """Switch to an unseen floor plan dynamically."""
        self.building = Building.create_by_plan(plan_type, width=34, height=22)
        self.manager.building = self.building
        self.resolver.building = self.building
        self.blocked_exits.clear()
        self.rerouted_count = 0
        self.current_tick = 0
        self.state = SimulationState.STOPPED
        self.manager.spawn_agents(count=self.agent_count, seed=self.seed)
        self.setup_agent_routes()

    def cycle_floor_plan(self) -> str:
        """Cycle to the next available floor plan."""
        current_idx = 0
        if self.building.plan_type in Building.AVAILABLE_PLANS:
            current_idx = Building.AVAILABLE_PLANS.index(self.building.plan_type)
        next_idx = (current_idx + 1) % len(Building.AVAILABLE_PLANS)
        next_plan = Building.AVAILABLE_PLANS[next_idx]
        self.load_floor_plan(next_plan)
        return next_plan

    def add_hazard(self, gx: int, gy: int) -> bool:
        if self.building.add_hazard(gx, gy):
            self.setup_agent_routes()
            return True
        return False

    def remove_hazard(self, gx: int, gy: int) -> bool:
        if self.building.remove_hazard(gx, gy):
            self.setup_agent_routes()
            return True
        return False

    def spawn_agent_at(self, x: float, y: float) -> Optional[Agent]:
        agent = self.manager.spawn_single_at(x, y)
        if agent:
            if self.crowd_mode == CrowdMode.EVACUATION:
                field = MultiSourceDistanceField(self.building.grid, self.building.grid.get_exits())
                path = field.get_path_from(agent.current_pos)
                if path:
                    agent.set_path(path, target_exit=path[-1])
            else:
                rng = random.Random()
                pools = [c for c in self.building.grid.get_exits() if self.building.grid.is_walkable(c[0], c[1])]
                target = rng.choice(pools) if pools else (15, 15)
                path = bfs_shortest_path(self.building.grid, agent.current_pos, [target])
                if path:
                    agent.set_path(path, target_exit=target)
        return agent

    def start(self) -> None:
        if self.state in (SimulationState.STOPPED, SimulationState.PAUSED):
            if self.current_tick == 0:
                self.setup_agent_routes()
            self.state = SimulationState.RUNNING

    def pause(self) -> None:
        if self.state == SimulationState.RUNNING:
            self.state = SimulationState.PAUSED

    def resume(self) -> None:
        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING

    def step(self, dt: float = 0.05) -> None:
        """Execute one continuous physics integration tick."""
        if self.state != SimulationState.RUNNING:
            return

        self.current_tick += 1

        # Advance Helbing Social Force physics
        self.resolver.step(self.current_tick, dt=dt)

        # Dynamic Congestion Rerouting check (every 8 ticks)
        if self.current_tick % 8 == 0:
            self.check_congestion_rerouting()

        # In NORMAL_FLOW: Keep crowd circulating continuously
        if self.crowd_mode == CrowdMode.NORMAL_FLOW:
            grid = self.building.grid
            rng = random.Random(self.seed + self.current_tick * 13)
            for agent in self.manager.agents:
                if agent.is_evacuated or (agent.is_active and agent.next_intended_cell is None):
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

        # In EVACUATION mode: check completion
        elif self.crowd_mode == CrowdMode.EVACUATION:
            if self.manager.is_evacuation_complete:
                self.state = SimulationState.COMPLETED

    def reset(self) -> None:
        self.state = SimulationState.STOPPED
        self.current_tick = 0
        self.rerouted_count = 0

        for bx, by in list(self.blocked_exits):
            self.building.grid.set_cell(bx, by, CellType.EXIT)
        self.blocked_exits.clear()

        for hx, hy in list(self.building.hazards):
            self.building.remove_hazard(hx, hy)

        self.manager.reset_all()
        self.setup_agent_routes()

    def restart_with_new_seed(self, new_seed: Optional[int] = None) -> None:
        if new_seed is not None:
            self.seed = new_seed
        else:
            self.seed += 1

        self.state = SimulationState.STOPPED
        self.current_tick = 0
        self.rerouted_count = 0

        for bx, by in list(self.blocked_exits):
            self.building.grid.set_cell(bx, by, CellType.EXIT)
        self.blocked_exits.clear()

        for hx, hy in list(self.building.hazards):
            self.building.remove_hazard(hx, hy)

        self.manager.spawn_agents(count=self.agent_count, seed=self.seed)
        self.setup_agent_routes()

    def toggle_exit_block(self, exit_coord: Tuple[int, int]) -> bool:
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
        return self.metrics.get_summary(self.current_tick)
