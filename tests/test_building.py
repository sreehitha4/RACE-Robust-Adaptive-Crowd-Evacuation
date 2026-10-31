"""Unit tests for Grid and Building environment implementations.

Verifies boundary conditions, collision detection, architectural layout,
doorway placements, and reachability of emergency exits.
"""

import pytest
from collections import deque
from environment.grid import CellType, Grid
from environment.building import Building, Room


class TestGridBasics:
    """Test suite for basic Grid primitives."""

    def test_grid_initialization(self) -> None:
        grid = Grid(width=10, height=5, default_cell=CellType.FLOOR)
        assert grid.width == 10
        assert grid.height == 5
        assert grid.get_cell(0, 0) == CellType.FLOOR
        assert grid.get_cell(9, 4) == CellType.FLOOR

    def test_invalid_dimensions(self) -> None:
        with pytest.raises(ValueError):
            Grid(width=0, height=5)
        with pytest.raises(ValueError):
            Grid(width=5, height=-1)

    def test_boundary_checks(self) -> None:
        grid = Grid(5, 5)
        assert grid.is_inside(0, 0) is True
        assert grid.is_inside(4, 4) is True
        assert grid.is_inside(-1, 0) is False
        assert grid.is_inside(0, 5) is False
        assert grid.is_inside(5, 5) is False

    def test_out_of_bounds_access_raises_error(self) -> None:
        grid = Grid(5, 5)
        with pytest.raises(IndexError):
            grid.get_cell(5, 0)
        with pytest.raises(IndexError):
            grid.set_cell(-1, 2, CellType.WALL)

    def test_cell_type_mutation_and_checks(self) -> None:
        grid = Grid(4, 4, default_cell=CellType.FLOOR)
        assert grid.is_walkable(1, 1) is True
        assert grid.is_wall(1, 1) is False
        assert grid.is_exit(1, 1) is False

        grid.set_cell(1, 1, CellType.WALL)
        assert grid.is_walkable(1, 1) is False
        assert grid.is_wall(1, 1) is True
        assert grid.is_exit(1, 1) is False

        grid.set_cell(2, 2, CellType.EXIT)
        assert grid.is_walkable(2, 2) is True
        assert grid.is_wall(2, 2) is False
        assert grid.is_exit(2, 2) is True

    def test_get_neighbors_four_directional(self) -> None:
        grid = Grid(3, 3, default_cell=CellType.FLOOR)
        # Center cell (1, 1) has 4 neighbors: (1, 0), (1, 2), (0, 1), (2, 1)
        neighbors = grid.get_neighbors(1, 1)
        assert len(neighbors) == 4
        assert (1, 0) in neighbors
        assert (1, 2) in neighbors
        assert (0, 1) in neighbors
        assert (2, 1) in neighbors

        # Add a wall to the right (2, 1)
        grid.set_cell(2, 1, CellType.WALL)
        neighbors_after_wall = grid.get_neighbors(1, 1)
        assert len(neighbors_after_wall) == 3
        assert (2, 1) not in neighbors_after_wall

        # Corner cell (0, 0) should only have 2 in-bounds neighbors
        corner_neighbors = grid.get_neighbors(0, 0)
        assert len(corner_neighbors) == 2
        assert (1, 0) in corner_neighbors
        assert (0, 1) in corner_neighbors


class TestBuildingLayout:
    """Test suite for the architectural building layout."""

    @pytest.fixture
    def building(self) -> Building:
        return Building.create_default(width=30, height=20)

    def test_default_building_dimensions(self, building: Building) -> None:
        assert building.grid.width == 30
        assert building.grid.height == 20

    def test_room_specifications(self, building: Building) -> None:
        room_names = list(building.rooms.keys())
        assert len(room_names) == 4  # 3 rooms + 1 corridor
        assert any("Room A" in name for name in room_names)
        assert any("Room B" in name for name in room_names)
        assert any("Room C" in name for name in room_names)
        assert any("Corridor" in name for name in room_names)

    def test_exits_exist_and_walkable(self, building: Building) -> None:
        exits = building.grid.get_exits()
        assert len(exits) >= 2
        for ex, ey in exits:
            assert building.grid.is_exit(ex, ey) is True
            assert building.grid.is_walkable(ex, ey) is True

    def test_exterior_perimeter_is_solid_except_exits(self, building: Building) -> None:
        grid = building.grid
        for x in range(grid.width):
            for y in [0, grid.height - 1]:
                if not grid.is_exit(x, y):
                    assert grid.is_wall(x, y) is True
        for y in range(grid.height):
            for x in [0, grid.width - 1]:
                if not grid.is_exit(x, y):
                    assert grid.is_wall(x, y) is True

    def test_doorways_are_open(self, building: Building) -> None:
        grid = building.grid
        for room in building.rooms.values():
            for dx, dy in room.doorways:
                assert grid.is_walkable(dx, dy) is True
                assert grid.get_cell(dx, dy) == CellType.FLOOR

    def test_full_connectivity_to_exits(self, building: Building) -> None:
        """Verify using BFS flood-fill that every single walkable floor cell
        in the building can reach at least one emergency exit.
        """
        grid = building.grid
        exits = grid.get_exits()
        assert len(exits) > 0

        # Multi-source BFS flood fill from all exits
        queue = deque(exits)
        visited = set(exits)

        while queue:
            cx, cy = queue.popleft()
            for nx, ny in grid.get_neighbors(cx, cy):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        # Check every cell in the grid
        unreachable_cells = []
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.is_walkable(x, y) and (x, y) not in visited:
                    unreachable_cells.append((x, y))

        assert len(unreachable_cells) == 0, (
            f"Found {len(unreachable_cells)} unreachable walkable cells: {unreachable_cells[:10]}"
        )


    @pytest.mark.parametrize("plan_type", [
        Building.FLOOR_PLAN_OFFICE,
        Building.FLOOR_PLAN_TERMINAL,
        Building.FLOOR_PLAN_PROCEDURAL
    ])
    def test_unseen_floor_plans_connectivity(self, plan_type: str) -> None:
        """Verify that any unseen architectural layout has 100% exit connectivity."""
        building = Building.create_by_plan(plan_type)
        grid = building.grid
        exits = grid.get_exits()
        assert len(exits) >= 2

        queue = deque(exits)
        visited = set(exits)

        while queue:
            cx, cy = queue.popleft()
            for nx, ny in grid.get_neighbors(cx, cy):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        unreachable = []
        for y in range(grid.height):
            for x in range(grid.width):
                if grid.is_walkable(x, y) and (x, y) not in visited:
                    unreachable.append((x, y))

        assert len(unreachable) == 0, f"Unseen plan '{plan_type}' has unreachable cells: {unreachable}"

    def test_architectural_obstacles_placement(self, building: Building) -> None:
        """Verify the 4 architectural obstacles (Kiosk, Bench, Planter, Desk) are registered and solid."""
        assert len(building.obstacles) >= 4
        obstacle_types = set(building.obstacles.values())
        assert "KIOSK" in obstacle_types
        assert "BENCH" in obstacle_types
        assert "PLANTER" in obstacle_types
        assert "DESK" in obstacle_types

        # Verify that all obstacles act as solid walls
        for (ox, oy), obs_type in building.obstacles.items():
            assert building.grid.is_wall(ox, oy) is True
            assert building.grid.is_walkable(ox, oy) is False
