from pathlib import Path

import numpy as np

from .agent import PedestrianAgent
from .collision import CollisionAvoidance
from .config import SimulationConfig
from .environment import Environment
from .ml_integration import MLTrajectoryAdapter
from .movement import MovementController
from .obstacle import ObstacleHandler
from .statistics import EvacuationStatistics
from .trajectory import TrajectoryManager


class CrowdSimulation:
    """Headless, deterministic crowd simulation with optional RACE LSTM guidance."""

    def __init__(
        self,
        config=None,
        environment=None,
        predictor=None,
        project_root=None
    ):
        self.config = config or SimulationConfig()
        self.config.validate()

        self.project_root = Path(
            project_root or Path(__file__).resolve().parents[1]
        )

        self.environment = environment or Environment(
            self.config.room_width,
            self.config.room_height
        )

        checkpoint = self.project_root / self.config.checkpoint_path

        self.ml = MLTrajectoryAdapter(
            checkpoint if self.config.use_ml else None,
            predictor=predictor
        )

        self.trajectory = TrajectoryManager(
            self.config.sample_interval_seconds
        )

        self.collision = CollisionAvoidance(
            self.config.separation_distance,
            self.config.separation_weight
        )

        self.obstacles = ObstacleHandler(
            self.environment,
            self.config.obstacle_clearance
        )

        self.movement = MovementController(
            self.config,
            self.environment,
            self.collision,
            self.obstacles
        )

        self.rng = np.random.default_rng(
            self.config.random_seed
        )

        self.time = 0.0
        self.status = "ready"

        self.coordinate_system = (
            "ETH-UCY-compatible x/y coordinate units; "
            "not asserted to be metres"
        )

        # Tracks agents already counted as evacuated.
        self._counted_evacuations = set()

        self.agents = self._create_agents(
            self.config.agent_count
        )

        self.statistics = EvacuationStatistics(
            len(self.agents)
        )

        for agent in self.agents:
            self.trajectory.sample(
                agent,
                0.0,
                force=True
            )

    # --------------------------------------------------
    # AGENT INITIALIZATION
    # --------------------------------------------------

    def _create_agents(self, count):

        agents = []
        attempts = 0

        while len(agents) < count and attempts < count * 500:

            attempts += 1

            x = self.rng.uniform(
                2.0,
                self.environment.width - 2.0
            )

            y = self.rng.uniform(
                1.0,
                self.environment.height - 1.0
            )

            if not self.environment.is_walkable(
                x,
                y,
                self.config.agent_radius,
                self.config.obstacle_clearance
            ):
                continue

            if any(
                np.linalg.norm(
                    np.array([x, y]) - agent.position
                ) < 2.2 * self.config.agent_radius
                for agent in agents
            ):
                continue

            # Select the farther-side exit.
            exit_obj = min(
                self.environment.exits,
                key=lambda e: abs(e.x - x)
            )

            far_exit = max(
                self.environment.exits,
                key=lambda e: abs(e.x - x)
            )

            goal = (
                far_exit
                if abs(far_exit.x - x) > abs(exit_obj.x - x)
                else exit_obj
            )

            agent = PedestrianAgent(
                len(agents) + 1,
                np.array([x, y]),
                goal.id,
                self.config.agent_radius
            )

            agent.navigation_path = self.environment.find_path(
                agent.position,
                (goal.x, goal.y),
                agent.radius,
                self.config.obstacle_clearance
            )

            agents.append(agent)

        if len(agents) != count:
            raise RuntimeError(
                f"Could only place {len(agents)} of {count} agents; "
                "reduce count or obstacles."
            )

        return agents

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    def reset(self):

        config = self.config
        project_root = self.project_root
        predictor = self.ml.predictor

        self.__init__(
            config=config,
            environment=Environment(
                config.room_width,
                config.room_height
            ),
            predictor=predictor,
            project_root=project_root
        )

        return self.state()

    # --------------------------------------------------
    # LSTM PREDICTION
    # --------------------------------------------------

    def _update_predictions(self, sampled_agents):

        if not self.ml.enabled:
            return

        for agent in sampled_agents:

            observed = self.trajectory.model_input(agent)

            if observed is None:
                continue

            try:

                agent.predicted_trajectory = self.ml.predict(
                    observed
                )

                agent.last_prediction_at = self.time

            except Exception as exc:

                self.last_ml_error = (
                    f"Agent {agent.id}: {exc}"
                )

    # --------------------------------------------------
    # SIMULATION STEP
    # --------------------------------------------------

    def step(self, steps=1):

        if steps < 1:
            raise ValueError("steps must be >= 1")

        self.status = "running"

        for _ in range(steps):

            # Stop if simulation has reached its limit
            # or all pedestrians have evacuated.

            if (
                self.time >= self.config.max_simulation_seconds
                or all(
                    agent.state == "evacuated"
                    for agent in self.agents
                )
            ):
                self.status = "completed"
                break

            sampled = []

            # Record trajectories and update predictions.

            for agent in self.agents:

                if agent.state == "evacuated":
                    continue

                if self.trajectory.sample(
                    agent,
                    self.time
                ):
                    sampled.append(agent)

            self._update_predictions(sampled)

            # Only active pedestrians participate in movement.

            active = [
                agent
                for agent in self.agents
                if agent.state != "evacuated"
            ]

            # Use the same pre-update snapshot for all agents.

            self.collision.prepare(active, bounds=(0.0, 0.0, self.environment.width, self.environment.height),
                                   query_margin=2.0 * self.config.max_speed * self.config.dt)

            updates = [
                (agent, agent.predicted_trajectory)
                for agent in active
            ]

            for agent, prediction in updates:

                if agent.state == "evacuated":
                    continue

                self.movement.update_agent(
                    agent,
                    active,
                    self.config.dt,
                    prediction
                )

            # Advance simulation time.

            self.time = round(
                self.time + self.config.dt,
                8
            )

            # ------------------------------------------
            # EVACUATION DETECTION
            # ------------------------------------------

            for agent in active:

                # Do not process an already evacuated agent.

                if agent.state == "evacuated":
                    continue

                # Do not count the same agent twice.

                if agent.id in self._counted_evacuations:
                    continue

                exit_obj = next(
                    (
                        exit_item
                        for exit_item in self.environment.exits
                        if exit_item.id == agent.goal_exit_id
                    ),
                    None
                )

                if exit_obj is None:
                    continue

                exit_position = np.array([
                    exit_obj.x,
                    exit_obj.y
                ])

                distance = np.linalg.norm(
                    agent.position - exit_position
                )

                if distance <= self.config.exit_radius:

                    agent.state = "evacuated"

                    agent.velocity[:] = 0.0

                    agent.evacuated_at = self.time

                    # Record this agent exactly once.

                    self._counted_evacuations.add(
                        agent.id
                    )

                    self.statistics.mark_evacuated(
                        self.time,
                        agent_id=agent.id
                    )

            # ------------------------------------------
            # COMPLETION CHECK
            # ------------------------------------------

            if all(
                agent.state == "evacuated"
                for agent in self.agents
            ):
                self.status = "completed"
                break

        return self.state()

    # --------------------------------------------------
    # RUN FULL SIMULATION
    # --------------------------------------------------

    def run(self, duration_seconds=None):

        duration = (
            duration_seconds
            if duration_seconds is not None
            else self.config.max_simulation_seconds
        )

        count = max(
            1,
            int(duration / self.config.dt)
        )

        for _ in range(count):

            if self.status == "completed":
                break

            self.step()

        return self.state()

    # --------------------------------------------------
    # EXPORT CURRENT STATE
    # --------------------------------------------------

    def state(self):

        from .export import StateExporter

        return StateExporter.to_dict(self)
