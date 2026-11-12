import numpy as np

class MovementController:
    def __init__(self, config, environment, collision, obstacle_handler):
        self.config, self.environment = config, environment
        self.collision, self.obstacles = collision, obstacle_handler

    @staticmethod
    def _unit(vector):
        n = float(np.linalg.norm(vector))
        return vector/n if n > 1e-9 else np.zeros(2)

    def desired_velocity(self, agent, agents, prediction=None):
        exit_obj = next(e for e in self.environment.exits if e.id == agent.goal_exit_id)
        if agent.navigation_path:
            while agent.waypoint_index < len(agent.navigation_path)-1 and np.linalg.norm(np.asarray(agent.navigation_path[agent.waypoint_index])-agent.position) < 0.45:
                agent.waypoint_index += 1
            target = np.asarray(agent.navigation_path[min(agent.waypoint_index, len(agent.navigation_path)-1)])
        else:
            target = np.array([exit_obj.x, exit_obj.y])
        goal = self._unit(target - agent.position)
        direction = self.config.goal_weight * goal
        if prediction is not None and len(prediction):
            # Prediction is a preference only; use the first future displacement as a heading cue.
            pred_direction = self._unit(np.asarray(prediction[0]) - agent.position)
            if np.linalg.norm(pred_direction) > 0:
                direction += self.config.prediction_weight * pred_direction
        direction += self.collision.separation_vector(agent, agents)
        direction = self._unit(direction)
        return direction * self.config.preferred_speed

    def update_agent(self, agent, agents, dt, prediction=None):
        velocity = self.desired_velocity(agent, agents, prediction)
        speed = float(np.linalg.norm(velocity))
        if speed > self.config.max_speed:
            velocity = velocity / speed * self.config.max_speed
        velocity = self.obstacles.safe_velocity(agent.position, velocity, dt, agent.radius)
        # Hard one-step overlap check supplements the soft separation steering.
        # Try nearby headings; if none is safe, stop rather than intentionally overlap.
        candidate_velocity = velocity
        for angle in (0.0, 0.45, -0.45, 0.9, -0.9, 1.35, -1.35, 1.8, -1.8):
            c, s = np.cos(angle), np.sin(angle)
            trial = np.array([c*velocity[0]-s*velocity[1], s*velocity[0]+c*velocity[1]])
            candidate = agent.position + trial * dt
            if not self.obstacles.is_position_safe(candidate, agent.radius):
                continue
            collision = False
            for other in agents:
                if other.id == agent.id or other.state == "evacuated":
                    continue
                minimum = agent.radius + other.radius
                if np.linalg.norm(candidate - other.position) < minimum - 1e-6:
                    collision = True
                    break
            if not collision:
                candidate_velocity = trial
                break
        else:
            candidate_velocity = np.zeros(2)
        candidate = agent.position + candidate_velocity * dt
        if self.obstacles.is_position_safe(candidate, agent.radius):
            agent.position = candidate
            agent.velocity = candidate_velocity
        else:
            agent.velocity = np.zeros(2)
