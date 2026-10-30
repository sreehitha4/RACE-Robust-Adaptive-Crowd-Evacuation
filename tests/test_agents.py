"""Unit tests for Agent and AgentManager classes."""

import pytest
from environment.building import Building
from environment.grid import CellType
from agents.agent import Agent, AgentState
from agents.manager import AgentManager


class TestAgent:
    """Test suite for the Agent entity."""

    def test_agent_initialization(self) -> None:
        agent = Agent(agent_id=1, start_pos=(5, 5))
        assert agent.agent_id == 1
        assert agent.start_pos == (5, 5)
        assert agent.current_pos == (5, 5)
        assert agent.state == AgentState.ACTIVE
        assert agent.is_active is True
        assert agent.steps_taken == 0
        assert agent.wait_ticks == 0

    def test_agent_path_and_advance(self) -> None:
        agent = Agent(agent_id=1, start_pos=(5, 5))
        path = [(5, 5), (5, 6), (5, 7)]
        agent.set_path(path, target_exit=(5, 7))

        assert agent.next_intended_cell == (5, 6)
        agent.advance_to((5, 6))
        assert agent.current_pos == (5, 6)
        assert agent.steps_taken == 1
        assert agent.next_intended_cell == (5, 7)

    def test_agent_state_transitions(self) -> None:
        agent = Agent(agent_id=1, start_pos=(5, 5))
        agent.record_wait()
        assert agent.wait_ticks == 1

        agent.mark_evacuated(current_tick=42)
        assert agent.is_evacuated is True
        assert agent.evacuation_tick == 42

        agent.reset()
        assert agent.is_active is True
        assert agent.current_pos == (5, 5)
        assert agent.evacuation_tick is None
        assert agent.wait_ticks == 0


class TestAgentManager:
    """Test suite for AgentManager population management."""

    @pytest.fixture
    def manager(self) -> AgentManager:
        building = Building.create_default()
        return AgentManager(building)

    def test_spawn_agents_count_and_validity(self, manager: AgentManager) -> None:
        agents = manager.spawn_agents(count=20, seed=123)
        assert manager.total_count == 20
        assert len(agents) == 20

        grid = manager.building.grid
        seen_positions = set()

        for agent in agents:
            x, y = agent.start_pos
            # Must be in bounds
            assert grid.is_inside(x, y) is True
            # Must be walkable floor
            assert grid.is_walkable(x, y) is True
            # Must NOT be a wall
            assert not grid.is_wall(x, y)
            # Must NOT be an exit
            assert not grid.is_exit(x, y)
            # Must have unique starting position
            assert (x, y) not in seen_positions
            seen_positions.add((x, y))

    def test_reproducible_seed(self, manager: AgentManager) -> None:
        agents1 = manager.spawn_agents(count=15, seed=999)
        positions1 = [a.start_pos for a in agents1]

        agents2 = manager.spawn_agents(count=15, seed=999)
        positions2 = [a.start_pos for a in agents2]

        assert positions1 == positions2

    def test_occupancy_tracking(self, manager: AgentManager) -> None:
        manager.spawn_agents(count=5, seed=42)
        occupied = manager.get_occupied_cells()
        assert len(occupied) == 5

        # Mark one evacuated; occupied count drops to 4
        manager.agents[0].mark_evacuated(10)
        assert len(manager.get_occupied_cells()) == 4
