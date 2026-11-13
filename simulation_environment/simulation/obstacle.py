import numpy as np

class ObstacleHandler:
    def __init__(self, environment, clearance=0.12):
        self.environment = environment
        self.clearance = clearance

    def is_position_safe(self, position, radius):
        return self.environment.is_walkable(float(position[0]), float(position[1]), radius, self.clearance)

    def safe_velocity(self, position, velocity, dt, radius):
        candidate = position + velocity * dt
        if self.is_position_safe(candidate, radius):
            return velocity
        # Try deterministic steering alternatives before stopping.
        speed = float(np.linalg.norm(velocity))
        if speed < 1e-9:
            return np.zeros(2)
        for angle in (0.55, -0.55, 1.05, -1.05, 1.57, -1.57, 2.2, -2.2):
            c, s = np.cos(angle), np.sin(angle)
            rotated = np.array([c*velocity[0]-s*velocity[1], s*velocity[0]+c*velocity[1]])
            if self.is_position_safe(position + rotated*dt, radius):
                return rotated
        return np.zeros(2)
