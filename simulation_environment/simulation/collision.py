import numpy as np
from .spatial_index import QuadTree

class CollisionAvoidance:
    """Local collision steering accelerated by a per-tick quadtree index."""
    def __init__(self, separation_distance=0.75, weight=1.15):
        self.separation_distance = float(separation_distance)
        self.weight = float(weight)
        self._index = QuadTree()
        self._max_radius = 0.3
        self._query_margin = 0.0
        self._prepared = False

    def prepare(self, agents, bounds=None, query_margin=0.0):
        active = [a for a in agents if a.state != "evacuated"]
        self._max_radius = max((float(a.radius) for a in active), default=0.3)
        self._query_margin = max(0.0, float(query_margin))
        self._index = QuadTree(active, bounds=bounds)
        self._prepared = True

    def nearby_agents(self, position, radius):
        # Positions in the index are the tick-start snapshot. Expand by the maximum
        # possible relative movement during one tick to avoid missing moved neighbours.
        return self._index.query_radius(float(position[0]), float(position[1]), radius + self._query_margin)

    def separation_vector(self, agent, agents):
        if not self._prepared:
            self.prepare(agents)
        force = np.zeros(2, dtype=np.float64)
        candidates = self.nearby_agents(agent.position, max(self.separation_distance, agent.radius+self._max_radius))
        for other in candidates:
            if other.id == agent.id or other.state == "evacuated":
                continue
            delta = agent.position - other.position
            distance = float(np.linalg.norm(delta))
            desired = max(self.separation_distance, agent.radius + other.radius)
            if 1e-9 < distance < desired:
                force += (delta / distance) * ((desired-distance)/desired)
            elif distance <= 1e-9:
                angle = ((agent.id * 37 + other.id * 17) % 360) * np.pi / 180
                force += np.array([np.cos(angle), np.sin(angle)])
        return force * self.weight
