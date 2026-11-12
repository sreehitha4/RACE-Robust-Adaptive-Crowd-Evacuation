import unittest
import numpy as np
from simulation import CrowdSimulation, SimulationConfig
from simulation.environment import Environment
from simulation.trajectory import TrajectoryManager

class FakePredictor:
    def __init__(self): self.calls = 0
    def predict(self, observed):
        self.calls += 1
        assert observed.shape == (8, 2)
        return np.repeat(observed[-1][None, :], 12, axis=0)

class SimulationTests(unittest.TestCase):
    def test_environment_blocks_obstacle(self):
        env = Environment(20, 14)
        self.assertFalse(env.is_walkable(7.5, 4.0, 0.2))
        self.assertTrue(env.is_walkable(3.0, 3.0, 0.2))

    def test_history_contract(self):
        from simulation.agent import PedestrianAgent
        agent = PedestrianAgent(1, [1, 1], "exit_west")
        manager = TrajectoryManager(0.4)
        for i in range(8):
            agent.position = np.array([float(i), float(i)])
            manager.sample(agent, i*0.4, force=True)
        self.assertEqual(manager.model_input(agent).shape, (8, 2))

    def test_simulation_produces_contract_and_steps(self):
        cfg = SimulationConfig(agent_count=6, use_ml=False, max_simulation_seconds=5)
        sim = CrowdSimulation(cfg)
        state = sim.step(5)
        self.assertEqual(len(state["agents"]), 6)
        self.assertIn("density", state)
        self.assertIn("simulation_time", state)
        self.assertGreater(state["simulation_time"], 0)
        for a in state["agents"]:
            self.assertIn("predicted_trajectory", a)
            self.assertTrue(np.isfinite([a["x"],a["y"],a["vx"],a["vy"]]).all())

    def test_agents_do_not_overlap_while_active(self):
        cfg = SimulationConfig(agent_count=12, use_ml=False, max_simulation_seconds=20)
        sim = CrowdSimulation(cfg)
        for _ in range(80):
            sim.step()
            active = [a for a in sim.agents if a.state != "evacuated"]
            for i, a in enumerate(active):
                for b in active[i+1:]:
                    self.assertGreaterEqual(np.linalg.norm(a.position-b.position) + 1e-5, a.radius+b.radius)

    def test_full_demo_crowd_evacuates_with_checkpoint(self):
        cfg = SimulationConfig(agent_count=8, use_ml=True, max_simulation_seconds=60)
        sim = CrowdSimulation(cfg)
        self.assertTrue(sim.ml.enabled, "Bundled RACE checkpoint should load")
        final = sim.run(60)
        self.assertEqual(final["remaining_agents"], 0)
        self.assertEqual(final["status"], "completed")
        self.assertTrue(all(len(a["predicted_trajectory"]) == 12 for a in final["agents"]))

    def test_ml_adapter_contract(self):
        fake = FakePredictor()
        cfg = SimulationConfig(agent_count=4, use_ml=False)
        sim = CrowdSimulation(cfg, predictor=fake)
        # Force each agent to have a complete history and request predictions.
        for a in sim.agents:
            for i in range(8): a.trajectory_history.append(np.array([i*0.1, i*0.1], dtype=np.float32))
        sim._update_predictions(sim.agents)
        self.assertTrue(sim.ml.enabled)
        self.assertEqual(fake.calls, 4)
        self.assertEqual(sim.agents[0].predicted_trajectory.shape, (12,2))

if __name__ == "__main__": unittest.main()
