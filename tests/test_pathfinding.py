"""Unit tests for BFS pathfinding algorithms.

Covers open grids, obstacles, mazes, multiple exits, unreachable cells,
boundary edges, and distance-field equivalence.
"""

import pytest
from environment.grid import CellType, Grid
from algorithms.pathfinding import bfs_shortest_path, MultiSourceDistanceField


class TestBFSPathfinding:
    """Test suite for single-source and multi-source BFS pathfinding."""

    def test_simple_open_grid(self) -> None:
        # 5x5 grid: (0, 0) to (4, 4) in Manhattan distance: 4 + 4 = 8 steps (9 coordinates)
        grid = Grid(5, 5, default_cell=CellType.FLOOR)
        path = bfs_shortest_path(grid, start=(0, 0), goals=[(4, 4)])
        assert path is not None
        assert len(path) == 9
        assert path[0] == (0, 0)
        assert path[-1] == (4, 4)

    def test_grid_containing_walls(self) -> None:
        # 5x5 grid with a vertical wall down column 2 except a gap at (2, 4)
        grid = Grid(5, 5, default_cell=CellType.FLOOR)
        for y in range(4):
            grid.set_cell(2, y, CellType.WALL)

        path = bfs_shortest_path(grid, start=(0, 0), goals=[(4, 0)])
        assert path is not None
        # Path must route down to (2, 4) to pass through the wall gap
        assert (2, 4) in path
        for pos in path:
            assert grid.is_walkable(pos[0], pos[1])

    def test_maze_navigation(self) -> None:
        # A 5x5 serpentine maze
        # S . # . G
        # # . # . #
        # # . . . #
        grid = Grid(5, 3, default_cell=CellType.WALL)
        # Corridor path
        corridor = [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2), (3, 1), (3, 0), (4, 0)]
        for x, y in corridor:
            grid.set_cell(x, y, CellType.FLOOR)

        path = bfs_shortest_path(grid, start=(0, 0), goals=[(4, 0)])
        assert path == corridor

    def test_multiple_exits_selects_closest(self) -> None:
        # Start at (2, 0). Exit A is at (0, 0) (dist=2). Exit B is at (4, 0) (dist=2).
        # Exit C is at (2, 4) (dist=4).
        grid = Grid(5, 5, default_cell=CellType.FLOOR)
        exits = [(0, 0), (2, 4)]
        path = bfs_shortest_path(grid, start=(2, 0), goals=exits)
        assert path is not None
        assert path[-1] == (0, 0)
        assert len(path) == 3  # (2, 0) -> (1, 0) -> (0, 0)

    def test_unreachable_target(self) -> None:
        # Completely seal off target
        grid = Grid(5, 5, default_cell=CellType.FLOOR)
        # Seal (4, 4) with walls at (3, 4) and (4, 3)
        grid.set_cell(3, 4, CellType.WALL)
        grid.set_cell(4, 3, CellType.WALL)

        path = bfs_shortest_path(grid, start=(0, 0), goals=[(4, 4)])
        assert path is None

    def test_start_already_at_exit(self) -> None:
        grid = Grid(5, 5, default_cell=CellType.FLOOR)
        path = bfs_shortest_path(grid, start=(2, 2), goals=[(2, 2)])
        assert path == [(2, 2)]

    def test_invalid_start_or_wall_start(self) -> None:
        grid = Grid(5, 5, default_cell=CellType.FLOOR)
        grid.set_cell(1, 1, CellType.WALL)

        # Start inside a wall
        assert bfs_shortest_path(grid, start=(1, 1), goals=[(4, 4)]) is None
        # Start out of bounds
        assert bfs_shortest_path(grid, start=(-1, 0), goals=[(4, 4)]) is None
        # Empty goals
        assert bfs_shortest_path(grid, start=(0, 0), goals=[]) is None


class TestMultiSourceDistanceField:
    """Test suite for multi-source reverse BFS potential fields."""

    def test_distance_field_calculation(self) -> None:
        grid = Grid(5, 1, default_cell=CellType.FLOOR)
        # Line grid: 0, 1, 2, 3, 4. Exits at 0 and 4.
        exits = [(0, 0), (4, 0)]
        for ex, ey in exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        field = MultiSourceDistanceField(grid, exits)
        assert field.get_distance((0, 0)) == 0
        assert field.get_distance((1, 0)) == 1
        assert field.get_distance((2, 0)) == 2
        assert field.get_distance((3, 0)) == 1
        assert field.get_distance((4, 0)) == 0

    def test_field_path_matches_bfs_path_length(self) -> None:
        grid = Grid(10, 10, default_cell=CellType.FLOOR)
        exits = [(0, 5), (9, 5)]
        for ex, ey in exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        field = MultiSourceDistanceField(grid, exits)
        field_path = field.get_path_from((5, 5))
        bfs_path = bfs_shortest_path(grid, start=(5, 5), goals=exits)

        assert field_path is not None
        assert bfs_path is not None
        assert len(field_path) == len(bfs_path)
