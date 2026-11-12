import numpy as np

class CollisionAvoidance:
    def __init__(self, separation_distance=0.75, weight=1.15):
        self.separation_distance = float(separation_distance)
        self.weight = float(weight)

    def separation_vector(self, agent, agents):
        force = np.zeros(2, dtype=np.float64)
        for other in agents:
            if other.id == agent.id or other.state == "evacuated":
                continue
            delta = agent.position - other.position
            distance = float(np.linalg.norm(delta))
            desired = max(self.separation_distance, agent.radius + other.radius)
            if 1e-9 < distance < desired:
                force += (delta / distance) * ((desired-distance)/desired)
            elif distance <= 1e-9:
                # Stable deterministic direction for coincident positions.
                angle = ((agent.id * 37 + other.id * 17) % 360) * np.pi / 180
                force += np.array([np.cos(angle), np.sin(angle)])
        return force * self.weight
