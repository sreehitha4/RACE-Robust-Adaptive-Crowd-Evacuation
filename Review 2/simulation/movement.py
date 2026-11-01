"""Continuous Social Force Movement Resolver.

Executes Helbing's Social Force Model (SFM) for real-time continuous crowd physics:
  - Global navigation via BFS potential gradient.
  - Continuous personal space repulsion.
  - Smooth obstacle and wall gliding.
  - Companion group cohesion forces (friends/pairs).
  - Hazard repulsion around dynamic fires.
"""

import math
from typing import Dict, List, Optional, Set, Tuple
from environment.building import Building
from simulation.physics import SocialForceModel, Vector2
from agents.agent import Agent, AgentState
from agents.manager import AgentManager


class MovementResolver:
    """Continuous crowd movement engine implementing Helbing's Social Force Model."""

    def __init__(self, building: Building, manager: AgentManager) -> None:
        self.building: Building = building
        self.manager: AgentManager = manager
        self.sfm: SocialForceModel = SocialForceModel()

    def step(self, current_tick: int, dt: float = 0.05) -> int:
        """Advance continuous crowd physics by time delta dt.

        Returns:
            Number of active agents that progressed towards their destination.
        """
        active_agents = self.manager.active_agents
        if not active_agents:
            return 0

        grid = self.building.grid
        moved_count = 0

        # Precompute companion positions for fast group cohesion lookup
        companion_map: Dict[int, Vector2] = {
            a.agent_id: a.pos for a in active_agents if a.companion_id is not None
        }

        # 1. Compute forces for each agent
        for i, agent in enumerate(active_agents):
            total_force = Vector2(0.0, 0.0)

            # A. Desired Force (Driving towards next BFS waypoint / exit)
            desired_dir = Vector2(0.0, 0.0)
            target = agent.next_intended_cell

            if target is not None:
                # Target waypoint center in continuous space
                target_pt = Vector2(target[0] + 0.5, target[1] + 0.5)
                desired_dir = target_pt - agent.pos

                # Check if close enough to advance to next waypoint
                if desired_dir.length() < 0.65:
                    if agent.path_index + 2 < len(agent.path):
                        agent.advance_to(target)
                        moved_count += 1
                        # Peek next
                        target = agent.next_intended_cell
                        if target is not None:
                            target_pt = Vector2(target[0] + 0.5, target[1] + 0.5)
                            desired_dir = target_pt - agent.pos
                    else:
                        # Near final waypoint/exit: continue driving straight into portal
                        pass

            f_desired = self.sfm.compute_desired_force(
                current_vel=agent.vel,
                desired_dir=desired_dir,
                desired_speed=agent.desired_speed,
                mass=agent.mass
            )
            total_force = total_force + f_desired

            # B. Social Repulsion from other agents
            for j, other in enumerate(active_agents):
                if i == j:
                    continue
                dist = agent.pos.distance_to(other.pos)
                if dist < 2.5:  # Interaction cutoff radius
                    f_repulsion = self.sfm.compute_agent_repulsion(
                        pos_i=agent.pos,
                        vel_i=agent.vel,
                        radius_i=agent.radius,
                        pos_j=other.pos,
                        vel_j=other.vel,
                        radius_j=other.radius
                    )
                    total_force = total_force + f_repulsion

            # C. Companion Group Cohesion (Attraction to friend if in a pair)
            if agent.companion_id and agent.companion_id in companion_map:
                comp_pos = companion_map[agent.companion_id]
                f_group = self.sfm.compute_group_cohesion(
                    pos=agent.pos,
                    companion_pos=comp_pos,
                    comfort_distance=1.4,
                    cohesion_strength=10.0
                )
                total_force = total_force + f_group

            # D. Wall and Obstacle Repulsion
            gx, gy = int(agent.pos.x), int(agent.pos.y)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    wx, wy = gx + dx, gy + dy
                    if grid.is_inside(wx, wy):
                        if grid.is_wall(wx, wy):
                            nearest_x = max(float(wx), min(agent.pos.x, float(wx + 1)))
                            nearest_y = max(float(wy), min(agent.pos.y, float(wy + 1)))
                            f_wall = self.sfm.compute_wall_repulsion(
                                pos=agent.pos,
                                radius=agent.radius,
                                nearest_wall_pt=Vector2(nearest_x, nearest_y)
                            )
                            total_force = total_force + f_wall
                    else:
                        # Out of bounds: only repel if NOT adjacent to an open exit portal
                        clamped_x = max(0, min(wx, grid.width - 1))
                        clamped_y = max(0, min(wy, grid.height - 1))
                        if not grid.is_exit(clamped_x, clamped_y):
                            nearest_x = max(float(wx), min(agent.pos.x, float(wx + 1)))
                            nearest_y = max(float(wy), min(agent.pos.y, float(wy + 1)))
                            f_wall = self.sfm.compute_wall_repulsion(
                                pos=agent.pos,
                                radius=agent.radius,
                                nearest_wall_pt=Vector2(nearest_x, nearest_y)
                            )
                            total_force = total_force + f_wall

            # E. Hazard / Fire Repulsion
            for hx, hy in self.building.hazards:
                hazard_center = Vector2(hx + 0.5, hy + 0.5)
                h_dist = agent.pos.distance_to(hazard_center)
                if h_dist < 3.0:
                    diff = agent.pos - hazard_center
                    n = diff.normalized()
                    f_hazard = n * (60.0 / max(0.2, h_dist))
                    total_force = total_force + f_hazard

            # 2. Integrate continuous motion
            agent.integrate_physics(total_force, dt=dt)

            # 3. Check if reached an emergency exit
            cur_gx, cur_gy = agent.current_pos
            is_at_exit = (
                grid.is_inside(cur_gx, cur_gy) and grid.is_exit(cur_gx, cur_gy)
            )
            # Also check distance to target exit if it is an exit
            if not is_at_exit and target is not None and grid.is_exit(target[0], target[1]):
                if agent.pos.distance_to(Vector2(target[0] + 0.5, target[1] + 0.5)) < 0.85:
                    is_at_exit = True

            if is_at_exit:
                agent.mark_evacuated(current_tick)

        return moved_count
