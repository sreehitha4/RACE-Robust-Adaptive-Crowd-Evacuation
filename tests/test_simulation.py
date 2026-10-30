"""Unit tests for SimulationEngine and MovementResolver.

Verifies live agent movement, collision prevention, head-on swap avoidance,
dynamic exit blocking, metrics, and state transitions.
"""

import pytest
from environment.building import Building
from environment.grid import CellType, Grid
from agents.agent import Agent, AgentState
from agents.manager import AgentManager
from simulation.movement import MovementResolver
from simulation.engine import SimulationEngine, SimulationState


class TestMovementAndCollisions:
    """Test suite for movement arbitration and collision handling."""

    def test_single_agent_movement_to_exit(self) -> None:
        building = Building.create_default()
        manager = AgentManager(building)
        resolver = MovementResolver(building, manager)

        # Agent placed adjacent to West Exit (0, 15)
        agent = Agent(agent_id=1, start_pos=(1, 15))
        agent.set_path([(1, 15), (0, 15)], target_exit=(0, 15))
        manager.agents.append(agent)
        manager._agents_by_id[1] = agent

        moved = resolver.step(current_tick=1)
        assert moved == 1
        assert agent.current_pos == (0, 15)
        assert agent.is_evacuated is True
        assert agent.evacuation_tick == 1

    def test_destination_contention_no_overlap(self) -> None:
        """Two agents competing for the exact same destination cell."""
        building = Building.create_default()
        manager = AgentManager(building)
        resolver = MovementResolver(building, manager)

        # Agent 1 at (2, 14), Agent 2 at (2, 16). Both want (2, 15)
        a1 = Agent(agent_id=1, start_pos=(2, 14))
        a1.set_path([(2, 14), (2, 15)])

        a2 = Agent(agent_id=2, start_pos=(2, 16))
        a2.set_path([(2, 16), (2, 15)])

        manager.agents.extend([a1, a2])
        manager._agents_by_id[1] = a1
        manager._agents_by_id[2] = a2

        moved = resolver.step(current_tick=1)
        # Exactly one agent moves, one stays
        assert moved == 1
        assert a1.current_pos != a2.current_pos
        assert (a1.current_pos == (2, 15) and a2.current_pos == (2, 16)) or \
               (a2.current_pos == (2, 15) and a1.current_pos == (2, 14))

    def test_head_on_swap_prevention(self) -> None:
        """Agent 1 at A wants B, Agent 2 at B wants A."""
        building = Building.create_default()
        manager = AgentManager(building)
        resolver = MovementResolver(building, manager)

        pos_a = (5, 15)
        pos_b = (6, 15)

        a1 = Agent(agent_id=1, start_pos=pos_a)
        a1.set_path([pos_a, pos_b])

        a2 = Agent(agent_id=2, start_pos=pos_b)
        a2.set_path([pos_b, pos_a])

        manager.agents.extend([a1, a2])
        manager._agents_by_id[1] = a1
        manager._agents_by_id[2] = a2

        moved = resolver.step(current_tick=1)
        # They cannot swap simultaneously; at most one can move or one yields
        assert not (a1.current_pos == pos_b and a2.current_pos == pos_a)
        # No overlap
        assert a1.current_pos != a2.current_pos


class TestSimulationEngineLifecycle:
    """Test suite for high-level simulation engine execution and metrics."""

    @pytest.fixture
    def engine(self) -> SimulationEngine:
        building = Building.create_default()
        return SimulationEngine(building, agent_count=10, seed=42)

    def test_initial_state(self, engine: SimulationEngine) -> None:
        assert engine.state == SimulationState.STOPPED
        assert engine.current_tick == 0
        assert engine.manager.total_count == 10
        assert len(engine.manager.active_agents) == 10

    def test_run_until_complete_evacuation(self, engine: SimulationEngine) -> None:
        engine.start()
        assert engine.state == SimulationState.RUNNING

        # Step until all evacuated or max limit reached
        max_ticks = 200
        while engine.state == SimulationState.RUNNING and engine.current_tick < max_ticks:
            engine.step()

        assert engine.state == SimulationState.COMPLETED
        summary = engine.get_summary()
        assert summary.evacuation_percentage == 100.0
        assert summary.evacuated_agents == 10
        assert summary.active_agents == 0
        assert summary.stuck_agents == 0
        assert summary.avg_evacuation_ticks > 0

    def test_reset_functionality(self, engine: SimulationEngine) -> None:
        engine.start()
        for _ in range(5):
            engine.step()
        assert engine.current_tick == 5

        engine.reset()
        assert engine.state == SimulationState.STOPPED
        assert engine.current_tick == 0
        assert len(engine.manager.active_agents) == 10
        for agent in engine.manager.agents:
            assert agent.current_pos == agent.start_pos

    def test_dynamic_exit_blocking_and_rerouting(self, engine: SimulationEngine) -> None:
        """Block West exit, verifying agents dynamically reroute to East exit."""
        # West exit: (0, 15) and (0, 16)
        engine.toggle_exit_block((0, 15))
        engine.toggle_exit_block((0, 16))

        # Check all active agent paths now point to East exits (x = 29)
        for agent in engine.manager.active_agents:
            if agent.path:
                assert agent.target_exit[0] == 29
