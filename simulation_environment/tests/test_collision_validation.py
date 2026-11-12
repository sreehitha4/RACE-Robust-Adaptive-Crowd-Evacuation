
import unittest
import numpy as np

from simulation.agent import PedestrianAgent
from simulation.collision import CollisionAvoidance


class TestCollisionAvoidance(unittest.TestCase):

    def setUp(self):
        self.collision = CollisionAvoidance(
            separation_distance=0.75,
            weight=1.15
        )

    def create_agent(self, agent_id, position, state="walking"):
        agent = PedestrianAgent(
            id=agent_id,
            position=np.array(position, dtype=np.float64),
            goal_exit_id="exit_east"
        )
        agent.state = state
        return agent

    def test_safe_distance(self):
        """Agents sufficiently far apart should have no separation force."""

        agent1 = self.create_agent(1, (0, 0))
        agent2 = self.create_agent(2, (1.0, 0))

        force = self.collision.separation_vector(
            agent1,
            [agent1, agent2]
        )

        np.testing.assert_array_almost_equal(
            force,
            np.array([0.0, 0.0])
        )

    def test_agents_too_close(self):
        """An agent should experience force away from a nearby agent."""

        agent1 = self.create_agent(1, (0, 0))
        agent2 = self.create_agent(2, (0.4, 0))

        force = self.collision.separation_vector(
            agent1,
            [agent1, agent2]
        )

        # Agent 2 is to the right of Agent 1.
        # Therefore, Agent 1 must be pushed towards negative X.
        self.assertLess(force[0], 0)

        # There should be no Y-direction force.
        self.assertAlmostEqual(force[1], 0.0)

    def test_coincident_agents(self):
        """Overlapping agents should produce a finite separation force."""

        agent1 = self.create_agent(1, (2, 2))
        agent2 = self.create_agent(2, (2, 2))

        force = self.collision.separation_vector(
            agent1,
            [agent1, agent2]
        )

        self.assertTrue(np.all(np.isfinite(force)))
        self.assertGreater(np.linalg.norm(force), 0)

    def test_evacuated_agents_are_ignored(self):
        """Evacuated agents should not affect collision avoidance."""

        agent1 = self.create_agent(1, (0, 0))
        agent2 = self.create_agent(
            2,
            (0.4, 0),
            state="evacuated"
        )

        force = self.collision.separation_vector(
            agent1,
            [agent1, agent2]
        )

        np.testing.assert_array_almost_equal(
            force,
            np.array([0.0, 0.0])
        )


if __name__ == "__main__":
    unittest.main()
