"""Continuous 2D Vector Mathematics and Helbing's Social Force Model (SFM).

Implements real-time continuous crowd physics:
  - Vector2D utility primitives (addition, dot product, normalization, distance).
  - Desired velocity acceleration towards BFS navigation gradient.
  - Inter-agent social repulsion (personal space comfort zone).
  - Wall and obstacle repulsion for smooth corner gliding.
  - Social group cohesion (pairs, friends, families).
  - Panic-dependent pushing and physical contact friction.
"""

from dataclasses import dataclass
import math
from typing import List, Optional, Tuple


@dataclass
class Vector2:
    """Lightweight, high-performance 2D vector for continuous crowd physics."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "Vector2":
        if scalar == 0:
            return Vector2(0.0, 0.0)
        return Vector2(self.x / scalar, self.y / scalar)

    def length_sq(self) -> float:
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> "Vector2":
        l = self.length()
        if l < 1e-6:
            return Vector2(0.0, 0.0)
        return Vector2(self.x / l, self.y / l)

    def distance_to(self, other: "Vector2") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def dot(self, other: "Vector2") -> float:
        return self.x * other.x + self.y * other.y

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


class SocialForceModel:
    """Helbing's Social Force Model (SFM) for human crowd dynamics.

    Parameters:
      - tau: Relaxation time to reach desired velocity.
      - A_agent, B_agent: Social repulsion strength and range between individuals.
      - A_wall, B_wall: Repulsion strength and range from walls and obstacles.
      - k_body: Body compression elasticity when in physical contact.
      - k_friction: Tangential friction between touching bodies.
    """

    def __init__(
        self,
        tau: float = 0.5,
        A_agent: float = 20.0,
        B_agent: float = 0.8,
        A_wall: float = 30.0,
        B_wall: float = 0.6,
        k_body: float = 120.0,
        k_friction: float = 40.0
    ) -> None:
        self.tau: float = tau
        self.A_agent: float = A_agent
        self.B_agent: float = B_agent
        self.A_wall: float = A_wall
        self.B_wall: float = B_wall
        self.k_body: float = k_body
        self.k_friction: float = k_friction

    def compute_desired_force(
        self,
        current_vel: Vector2,
        desired_dir: Vector2,
        desired_speed: float,
        mass: float = 70.0
    ) -> Vector2:
        """Force driving person towards their target destination: (v0 * e0 - v) * (m / tau)."""
        target_vel = desired_dir.normalized() * desired_speed
        accel = (target_vel - current_vel) / self.tau
        return accel * mass

    def compute_agent_repulsion(
        self,
        pos_i: Vector2,
        vel_i: Vector2,
        radius_i: float,
        pos_j: Vector2,
        vel_j: Vector2,
        radius_j: float
    ) -> Vector2:
        """Social psychological repulsion plus physical contact forces between two people."""
        diff = pos_i - pos_j
        dist = diff.length()
        if dist < 1e-4:
            # Prevent singularity if positions coincide exactly
            return Vector2(1.0, 0.0) * self.A_agent

        normal = diff / dist
        r_sum = radius_i + radius_j
        overlap = r_sum - dist

        # 1. Psychological comfort zone repulsion
        f_social = normal * (self.A_agent * math.exp((r_sum - dist) / self.B_agent))

        # 2. Physical touching contact force (compression + friction)
        if overlap > 0:
            # Physical pushing
            f_body = normal * (self.k_body * overlap)
            # Tangential friction
            tangent = Vector2(-normal.y, normal.x)
            rel_vel_tangent = (vel_j - vel_i).dot(tangent)
            f_fric = tangent * (self.k_friction * overlap * rel_vel_tangent)
            return f_social + f_body + f_fric

        return f_social

    def compute_wall_repulsion(
        self,
        pos: Vector2,
        radius: float,
        nearest_wall_pt: Vector2
    ) -> Vector2:
        """Repulsion keeping agent from scraping or walking through solid walls."""
        diff = pos - nearest_wall_pt
        dist = diff.length()
        if dist < 1e-4:
            return Vector2(0.0, -1.0) * self.A_wall

        normal = diff / dist
        overlap = radius - dist

        f_wall = normal * (self.A_wall * math.exp((radius - dist) / self.B_wall))
        if overlap > 0:
            f_wall = f_wall + normal * (self.k_body * overlap)

        return f_wall

    def compute_group_cohesion(
        self,
        pos: Vector2,
        companion_pos: Vector2,
        comfort_distance: float = 1.2,
        cohesion_strength: float = 12.0
    ) -> Vector2:
        """Attraction force keeping friends or pairs together."""
        diff = companion_pos - pos
        dist = diff.length()
        if dist > comfort_distance:
            # Gently pull towards companion if falling behind
            direction = diff / dist
            pull = (dist - comfort_distance) * cohesion_strength
            return direction * min(pull, 25.0)
        return Vector2(0.0, 0.0)
