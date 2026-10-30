"""Breadth-First Search (BFS) pathfinding module.

Provides both single-agent shortest-path discovery and multi-source reverse BFS
distance-field computation for multiple emergency exits on 2D unweighted grids.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple
from environment.grid import Grid


def bfs_shortest_path(
    grid: Grid,
    start: Tuple[int, int],
    goals: Set[Tuple[int, int]] | List[Tuple[int, int]]
) -> Optional[List[Tuple[int, int]]]:
    """Find the shortest path from start coordinate to any of the goal coordinates.

    Uses an unweighted Breadth-First Search (BFS) with a FIFO queue, guaranteeing
    the minimal number of steps.

    Args:
        grid: The building spatial grid.
        start: Starting (x, y) coordinates.
        goals: One or more target exit coordinates.

    Returns:
        List of coordinates from start to reached goal inclusive: [start, ..., goal],
        or None if no walkable path exists.
    """
    goal_set = set(goals)
    if not goal_set:
        return None

    sx, sy = start
    if not grid.is_inside(sx, sy) or not grid.is_walkable(sx, sy):
        return None

    # Trivial case: already at an exit
    if start in goal_set:
        return [start]

    # Queue stores coordinates to explore
    queue: deque[Tuple[int, int]] = deque([start])
    visited: Set[Tuple[int, int]] = {start}
    # parent map to reconstruct path: child -> parent
    parent: Dict[Tuple[int, int], Tuple[int, int]] = {}

    reached_goal: Optional[Tuple[int, int]] = None

    while queue:
        current = queue.popleft()
        cx, cy = current

        if current in goal_set:
            reached_goal = current
            break

        for neighbor in grid.get_neighbors(cx, cy):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    if reached_goal is None:
        return None

    # Reconstruct path from goal back to start
    path: List[Tuple[int, int]] = []
    curr = reached_goal
    while curr != start:
        path.append(curr)
        curr = parent[curr]
    path.append(start)
    path.reverse()
    return path


class MultiSourceDistanceField:
    """Computes an exact shortest-distance potential field from all exits simultaneously.

    Multi-source BFS begins at all reachable exit cells (distance = 0) and propagates
    outward across the entire building in O(V + E) time. Every cell learns:
      1. Its exact step-distance to the nearest exit.
      2. The optimal neighboring cell to step into.
    """

    def __init__(self, grid: Grid, exits: List[Tuple[int, int]]) -> None:
        self.grid: Grid = grid
        self.exits: List[Tuple[int, int]] = [e for e in exits if grid.is_walkable(e[0], e[1])]
        self.distances: Dict[Tuple[int, int], int] = {}
        self.next_step: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self.nearest_exit: Dict[Tuple[int, int], Tuple[int, int]] = {}

        self._compute_field()

    def _compute_field(self) -> None:
        """Run multi-source reverse BFS starting from all exits."""
        queue: deque[Tuple[int, int]] = deque()

        for exit_pos in self.exits:
            self.distances[exit_pos] = 0
            self.next_step[exit_pos] = exit_pos
            self.nearest_exit[exit_pos] = exit_pos
            queue.append(exit_pos)

        while queue:
            current = queue.popleft()
            cx, cy = current
            current_dist = self.distances[current]

            for nx, ny in self.grid.get_neighbors(cx, cy):
                neighbor = (nx, ny)
                if neighbor not in self.distances:
                    self.distances[neighbor] = current_dist + 1
                    # In reverse BFS, the neighbor's fastest route to exit is stepping into `current`
                    self.next_step[neighbor] = current
                    self.nearest_exit[neighbor] = self.nearest_exit[current]
                    queue.append(neighbor)

    def is_reachable(self, pos: Tuple[int, int]) -> bool:
        """Check if pos can reach any emergency exit."""
        return pos in self.distances

    def get_distance(self, pos: Tuple[int, int]) -> Optional[int]:
        """Return distance to nearest exit or None if unreachable."""
        return self.distances.get(pos)

    def get_path_from(self, start: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Extract the full shortest path from start to its nearest exit."""
        if not self.is_reachable(start):
            return None

        path: List[Tuple[int, int]] = [start]
        current = start
        visited_in_path: Set[Tuple[int, int]] = {start}

        while current not in self.exits:
            next_pos = self.next_step.get(current)
            if next_pos is None or next_pos in visited_in_path:
                # Cycle prevention safeguard
                break
            visited_in_path.add(next_pos)
            path.append(next_pos)
            current = next_pos

        return path
