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
    goals: Set[Tuple[int, int]] | List[Tuple[int, int]],
    hazards: Optional[Set[Tuple[int, int]]] = None
) -> Optional[List[Tuple[int, int]]]:
    """Find the shortest path from start coordinate to any of the goal coordinates,
    intelligently steering clear of active fire hazards when alternative paths exist.
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

    hazard_set = hazards or set()
    hazard_buffer: Set[Tuple[int, int]] = set()
    if hazard_set:
        for hx, hy in hazard_set:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx != 0 or dy != 0:
                        bx, by = hx + dx, hy + dy
                        if (bx, by) != start and (bx, by) not in goal_set:
                            hazard_buffer.add((bx, by))

    # Pass 1: Try to find a path that avoids the immediate fire hazard buffer completely
    if hazard_buffer:
        path = _run_bfs(grid, start, goal_set, avoid_cells=hazard_buffer)
        if path is not None:
            return path

    # Pass 2: Fallback (if no safe path exists without stepping near buffer)
    return _run_bfs(grid, start, goal_set, avoid_cells=None)


def _run_bfs(
    grid: Grid,
    start: Tuple[int, int],
    goal_set: Set[Tuple[int, int]],
    avoid_cells: Optional[Set[Tuple[int, int]]] = None
) -> Optional[List[Tuple[int, int]]]:
    avoid = avoid_cells or set()
    queue: deque[Tuple[int, int]] = deque([start])
    visited: Set[Tuple[int, int]] = {start}
    parent: Dict[Tuple[int, int], Tuple[int, int]] = {}
    reached_goal: Optional[Tuple[int, int]] = None

    while queue:
        current = queue.popleft()
        cx, cy = current

        if current in goal_set:
            reached_goal = current
            break

        for neighbor in grid.get_neighbors(cx, cy):
            if neighbor not in visited and (neighbor not in avoid or neighbor in goal_set):
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

    def __init__(
        self,
        grid: Grid,
        exits: List[Tuple[int, int]],
        hazards: Optional[Set[Tuple[int, int]]] = None
    ) -> None:
        self.grid: Grid = grid
        self.exits: List[Tuple[int, int]] = [e for e in exits if grid.is_walkable(e[0], e[1])]
        self.hazards: Set[Tuple[int, int]] = hazards or set()
        self.distances: Dict[Tuple[int, int], int] = {}
        self.next_step: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self.nearest_exit: Dict[Tuple[int, int], Tuple[int, int]] = {}

        self._compute_field()

    def _compute_field(self) -> None:
        """Run multi-source reverse BFS starting from all exits, prioritizing paths
        that maintain a realistic, safe clearance distance away from active fire hazards.
        """
        # Cells immediately adjacent to active fire (thermal danger zone)
        hazard_buffer: Set[Tuple[int, int]] = set()
        if self.hazards:
            for hx, hy in self.hazards:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        bx, by = hx + dx, hy + dy
                        if self.grid.is_inside(bx, by) and self.grid.is_walkable(bx, by):
                            hazard_buffer.add((bx, by))

        queue: deque[Tuple[int, int]] = deque()

        for exit_pos in self.exits:
            self.distances[exit_pos] = 0
            self.next_step[exit_pos] = exit_pos
            self.nearest_exit[exit_pos] = exit_pos
            queue.append(exit_pos)

        # Phase 1: Propagate across all walkable cells that stay clear of the fire buffer
        deferred_buffer_queue: deque[Tuple[Tuple[int, int], Tuple[int, int], int]] = deque()
        while queue:
            current = queue.popleft()
            cx, cy = current
            current_dist = self.distances[current]

            for nx, ny in self.grid.get_neighbors(cx, cy):
                neighbor = (nx, ny)
                if neighbor not in self.distances:
                    if neighbor in hazard_buffer:
                        # Defer exploring into hazard buffer so safe routes take absolute priority
                        deferred_buffer_queue.append((neighbor, current, current_dist + 1))
                    else:
                        self.distances[neighbor] = current_dist + 1
                        self.next_step[neighbor] = current
                        self.nearest_exit[neighbor] = self.nearest_exit[current]
                        queue.append(neighbor)

        # Phase 2: If any trapped cells can only be reached through the buffer, process them
        while deferred_buffer_queue:
            neighbor, parent, dist = deferred_buffer_queue.popleft()
            if neighbor not in self.distances:
                self.distances[neighbor] = dist
                self.next_step[neighbor] = parent
                self.nearest_exit[neighbor] = self.nearest_exit[parent]
                for nx, ny in self.grid.get_neighbors(neighbor[0], neighbor[1]):
                    nb = (nx, ny)
                    if nb not in self.distances:
                        deferred_buffer_queue.append((nb, neighbor, dist + 1))

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
