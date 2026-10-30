"""2D Grid Environment Representation.

Defines cell types, coordinate boundaries, walkability checks, and
neighbor exploration primitives for 2D spatial simulation.
"""

from enum import IntEnum
from typing import List, Tuple, Optional


class CellType(IntEnum):
    """Enumeration of building grid cell types."""
    FLOOR = 0
    WALL = 1
    EXIT = 2


class Grid:
    """Represents a 2D discrete grid for spatial simulation.

    Coordinates follow the Cartesian convention (x, y):
      - x: horizontal column index (0 <= x < width)
      - y: vertical row index (0 <= y < height)
    Internally cells are stored as cells[y][x].
    """

    # Orthogonal 4-directional moves: Up, Down, Left, Right
    CARDINAL_DELTAS: List[Tuple[int, int]] = [
        (0, -1),  # Up / North
        (0, 1),   # Down / South
        (-1, 0),  # Left / West
        (1, 0),   # Right / East
    ]

    def __init__(self, width: int, height: int, default_cell: CellType = CellType.FLOOR) -> None:
        """Initialize a grid with specified dimensions and default cell type.

        Args:
            width: Number of columns (must be positive).
            height: Number of rows (must be positive).
            default_cell: Initial cell type for all cells.
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Grid dimensions must be positive integers, got {width}x{height}")

        self.width: int = width
        self.height: int = height
        self._cells: List[List[int]] = [
            [int(default_cell) for _ in range(width)] for _ in range(height)
        ]

    def is_inside(self, x: int, y: int) -> bool:
        """Check if coordinate (x, y) falls within the grid boundaries."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cell(self, x: int, y: int) -> CellType:
        """Get the cell type at (x, y).

        Raises:
            IndexError: If coordinates are outside grid bounds.
        """
        if not self.is_inside(x, y):
            raise IndexError(f"Coordinate ({x}, {y}) is out of bounds for grid of size {self.width}x{self.height}")
        return CellType(self._cells[y][x])

    def set_cell(self, x: int, y: int, cell_type: CellType | int) -> None:
        """Set the cell type at (x, y).

        Raises:
            IndexError: If coordinates are outside grid bounds.
        """
        if not self.is_inside(x, y):
            raise IndexError(f"Coordinate ({x}, {y}) is out of bounds for grid of size {self.width}x{self.height}")
        self._cells[y][x] = int(cell_type)

    def is_walkable(self, x: int, y: int) -> bool:
        """Check if a cell is inside the grid and can be entered by an agent.

        Walls cannot be walked on; floors and exits are walkable.
        """
        if not self.is_inside(x, y):
            return False
        return self._cells[y][x] != CellType.WALL

    def is_wall(self, x: int, y: int) -> bool:
        """Check if coordinate is inside grid and is a wall."""
        if not self.is_inside(x, y):
            return False
        return self._cells[y][x] == CellType.WALL

    def is_exit(self, x: int, y: int) -> bool:
        """Check if coordinate is an emergency exit."""
        if not self.is_inside(x, y):
            return False
        return self._cells[y][x] == CellType.EXIT

    def get_exits(self) -> List[Tuple[int, int]]:
        """Retrieve coordinates of all exit cells in the grid."""
        exits: List[Tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if self._cells[y][x] == CellType.EXIT:
                    exits.append((x, y))
        return exits

    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Return all valid, walkable 4-directional neighboring coordinates."""
        neighbors: List[Tuple[int, int]] = []
        for dx, dy in self.CARDINAL_DELTAS:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny):
                neighbors.append((nx, ny))
        return neighbors

    def fill_rect(self, x1: int, y1: int, x2: int, y2: int, cell_type: CellType) -> None:
        """Fill an inclusive rectangular region [x1..x2, y1..y2] with cell_type."""
        min_x, max_x = max(0, min(x1, x2)), min(self.width - 1, max(x1, x2))
        min_y, max_y = max(0, min(y1, y2)), min(self.height - 1, max(y1, y2))
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                self._cells[y][x] = int(cell_type)

    def clone(self) -> "Grid":
        """Create a deep copy of this grid."""
        new_grid = Grid(self.width, self.height)
        new_grid._cells = [row.copy() for row in self._cells]
        return new_grid

    def to_ascii(self) -> str:
        """Render a readable ASCII representation of the grid for debugging."""
        symbols = {
            CellType.FLOOR: ".",
            CellType.WALL: "#",
            CellType.EXIT: "E",
        }
        lines: List[str] = []
        for y in range(self.height):
            line = "".join(symbols.get(CellType(self._cells[y][x]), "?") for x in range(self.width))
            lines.append(line)
        return "\n".join(lines)
