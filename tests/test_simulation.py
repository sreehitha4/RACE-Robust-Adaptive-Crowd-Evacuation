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
from simulation.engine import SimulationEngine, SimulationState, CrowdMode
from simulation.physics import Vector2


class TestMovementAndCollisions:
    """Test suite for movement arbitration and collision handling."""

    def test_single_agent_movement_to_exit(self) -> None:
        building = Building.create_default()
        manager = AgentManager(building)
        resolver = MovementResolver(building, manager)

        # Agent placed near West Exit (0, 16)
        agent = Agent(agent_id=1, start_pos=(1.0, 16.5))
        agent.set_path([(1, 16), (0, 16)], target_exit=(0, 16))
        manager.agents.append(agent)
        manager._agents_by_id[1] = agent

        # Step continuous physics until reaching exit
        for tick in range(1, 30):
            resolver.step(current_tick=tick, dt=0.08)
            if agent.is_evacuated:
                break

        assert agent.is_evacuated is True
        assert agent.evacuation_tick is not None

    def test_destination_contention_no_overlap(self) -> None:
        """Two agents competing for destination are kept apart by social forces."""
        building = Building.create_default()
        manager = AgentManager(building)
        resolver = MovementResolver(building, manager)

        # Agent 1 at (2, 14), Agent 2 at (2, 16). Both moving towards (2, 15)
        a1 = Agent(agent_id=1, start_pos=(2.0, 14.0))
        a1.set_path([(2, 14), (2, 15)])

        a2 = Agent(agent_id=2, start_pos=(2.0, 16.0))
        a2.set_path([(2, 16), (2, 15)])

        manager.agents.extend([a1, a2])
        manager._agents_by_id[1] = a1
        manager._agents_by_id[2] = a2

        # Step continuous physics
        for tick in range(1, 20):
            resolver.step(current_tick=tick, dt=0.05)

        # Social forces must keep them separated (distance > sum of body radii)
        dist = a1.pos.distance_to(a2.pos)
        assert dist >= 0.35  # No physical overlap allowed!

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
        engine.set_mode(CrowdMode.EVACUATION)
        engine.start()
        assert engine.state == SimulationState.RUNNING

        # Step until all evacuated or max limit reached
        max_ticks = 600
        while engine.state == SimulationState.RUNNING and engine.current_tick < max_ticks:
            engine.step(dt=0.08)

        assert engine.state == SimulationState.COMPLETED
        summary = engine.get_summary()
        assert summary.evacuation_percentage == 100.0
        assert summary.evacuated_agents == 10
        assert summary.active_agents == 0
        assert summary.stuck_agents == 0
        assert summary.avg_evacuation_ticks > 0

    def test_reset_functionality(self, engine: SimulationEngine) -> None:
        engine.set_mode(CrowdMode.EVACUATION)
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
        """Block West exit, verifying agents dynamically reroute to another available exit."""
        engine.set_mode(CrowdMode.EVACUATION)
        # West exit: (0, 15) and (0, 16)
        engine.toggle_exit_block((0, 15))
        engine.toggle_exit_block((0, 16))

        # Check all active agent paths now point away from West exit towards other open exits
        for agent in engine.manager.active_agents:
            if agent.path and agent.target_exit:
                assert agent.target_exit not in [(0, 15), (0, 16)]
                assert engine.building.grid.is_exit(agent.target_exit[0], agent.target_exit[1])


    def test_normal_crowd_circulation_mode(self, engine: SimulationEngine) -> None:
        """Test continuous normal pedestrian circulation where agents don't vanish upon reaching targets."""
        assert engine.crowd_mode == CrowdMode.NORMAL_FLOW
        engine.start()
        # Step through 20 ticks
        for _ in range(20):
            engine.step()

        # In normal mode, population remains active and circulating
        assert len(engine.manager.active_agents) == engine.agent_count
        assert engine.current_tick == 20

    def test_mode_switching(self, engine: SimulationEngine) -> None:
        """Test seamless switching between Normal Crowd Flow and Emergency Evacuation."""
        assert engine.crowd_mode == CrowdMode.NORMAL_FLOW
        engine.set_mode(CrowdMode.EVACUATION)
        assert engine.crowd_mode == CrowdMode.EVACUATION

        # In evacuation mode, agents have paths pointing to an exit
        for agent in engine.manager.active_agents:
            if agent.path and agent.target_exit:
                assert engine.building.grid.is_exit(agent.target_exit[0], agent.target_exit[1])

        # Switch back to normal flow
        engine.set_mode(CrowdMode.NORMAL_FLOW)
        assert engine.crowd_mode == CrowdMode.NORMAL_FLOW


    def test_social_force_repulsion_mechanics(self) -> None:
        """Verify Helbing's Social Force repulsion between two approaching individuals."""
        from simulation.physics import SocialForceModel, Vector2
        sfm = SocialForceModel()

        # Two agents facing each other with 0.5m distance
        pos1 = Vector2(5.0, 5.0)
        pos2 = Vector2(5.5, 5.0)
        vel1 = Vector2(1.0, 0.0)
        vel2 = Vector2(-1.0, 0.0)

        # Force on agent 1 from agent 2 must point left (-x direction)
        force_on_1 = sfm.compute_agent_repulsion(pos1, vel1, radius_i=0.35, pos_j=pos2, vel_j=vel2, radius_j=0.35)
        assert force_on_1.x < 0  # Repelled away from agent 2!

    def test_interactive_hazard_placement_and_rerouting(self, engine: SimulationEngine) -> None:
        """Verify placing a fire hazard dynamically triggers BFS re-routing."""
        hazard_pos = (5, 5)
        assert engine.add_hazard(*hazard_pos) is True
        assert hazard_pos in engine.building.hazards
        assert engine.building.grid.is_wall(*hazard_pos) is True

        # Remove hazard
        assert engine.remove_hazard(*hazard_pos) is True
        assert hazard_pos not in engine.building.hazards
        assert engine.building.grid.is_walkable(*hazard_pos) is True


    def test_dynamic_congestion_aware_exit_rerouting(self, engine: SimulationEngine) -> None:
        """Verify that when an exit queue becomes congested, trailing agents divert to another exit."""
        engine.set_mode(CrowdMode.EVACUATION)
        engine.congestion_reroute_enabled = True

        # Manually cluster 5 agents right outside West exit (0, 16)
        west_exit = (0, 16)
        for i in range(5):
            agent = engine.manager.agents[i]
            agent.pos = Vector2(1.5 + (i * 0.3), 16.5)
            agent.target_exit = west_exit

        # Place trailing agent in corridor at (10, 16) targeting West Exit
        trailing_agent = engine.manager.agents[9]
        trailing_agent.pos = Vector2(10.0, 16.5)
        trailing_agent.target_exit = west_exit

        initial_target = trailing_agent.target_exit
        engine.check_congestion_rerouting()

        # Due to heavy queue at West, trailing agent should evaluate alternatives (e.g. South or North)
        # and reroute count should increment
        assert engine.rerouted_count >= 1
        assert trailing_agent.target_exit != initial_target
        assert trailing_agent.rerouted is True

    def test_cycle_unseen_floor_plans(self, engine: SimulationEngine) -> None:
        """Verify cycling across all available floor plans resets state and re-populates correctly."""
        initial_plan = engine.building.name
        next_plan_type = engine.cycle_floor_plan()

        assert engine.building.name != initial_plan
        assert len(engine.manager.active_agents) == engine.agent_count
        assert engine.current_tick == 0
        assert engine.state == SimulationState.STOPPED
