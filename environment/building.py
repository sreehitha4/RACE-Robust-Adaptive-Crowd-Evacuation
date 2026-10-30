"""Building layout and architectural environment definition.

Defines rooms, corridors, walls, doorways, and multiple realistic building exits
(North Plaza Exit, South Main Entrance, West Wing Exit, and East Wing Exit),
ensuring all walkable areas have unobstructed connectivity to all exits.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .grid import CellType, Grid


@dataclass
class Room:
    """Represents an architectural room or zone within the building."""
    name: str
    x1: int
    y1: int
    x2: int
    y2: int
    doorways: List[Tuple[int, int]] = field(default_factory=list)

    def contains(self, x: int, y: int) -> bool:
        """Check if an interior point (x, y) is inside this room."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def get_interior_cells(self) -> List[Tuple[int, int]]:
        """Return all grid coordinates enclosed within this room."""
        cells: List[Tuple[int, int]] = []
        for y in range(self.y1, self.y2 + 1):
            for x in range(self.x1, self.x2 + 1):
                cells.append((x, y))
        return cells


class Building:
    """Represents a structured building containing rooms, corridors, and exits."""

    def __init__(self, grid: Grid, name: str = "University Complex") -> None:
        self.grid: Grid = grid
        self.name: str = name
        self.rooms: Dict[str, Room] = {}
        self.exits: List[Tuple[int, int]] = []

    def add_room(self, room: Room) -> None:
        """Register a room in the building."""
        self.rooms[room.name] = room

    @classmethod
    def create_default(cls, width: int = 30, height: int = 20) -> "Building":
        """Construct a realistic university complex floor plan with 4 distinct exits.

        Architecture:
          - Dimensions: 30 columns x 20 rows.
          - Perimeter: Solid exterior walls with 4 prominent exit portals.
          - Room A (West Wing): cols 1..8, rows 2..11.
          - Room B (Central Lecture Hall): cols 10..19, rows 2..11.
          - Room C (East Wing): cols 21..28, rows 2..11.
          - Main Concourse Corridor: cols 1..28, rows 13..18.
          - Exits:
              1. West Wing Exit: (0, 15), (0, 16)
              2. East Wing Exit: (width - 1, 15), (width - 1, 16)
              3. South Main Atrium Egress: (13, height - 1), (14, height - 1), (15, height - 1), (16, height - 1)
              4. North Plaza Exit: (14, 0), (15, 0)
        """
        grid = Grid(width, height, default_cell=CellType.FLOOR)

        # 1. Exterior Perimeter Walls
        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        # 2. Interior Dividing Walls
        # Vertical wall separating Room A and Room B
        grid.fill_rect(9, 1, 9, 12, CellType.WALL)
        # Vertical wall separating Room B and Room C
        grid.fill_rect(20, 1, 20, 12, CellType.WALL)
        # Horizontal wall separating all rooms from concourse corridor
        grid.fill_rect(1, 12, width - 2, 12, CellType.WALL)

        # 3. Create Doorways (wide 2-cell openings for natural crowd flow)
        room_a_doors = [(4, 12), (5, 12)]
        room_b_doors = [(14, 12), (15, 12)]
        room_c_doors = [(24, 12), (25, 12)]

        for dx, dy in room_a_doors + room_b_doors + room_c_doors:
            grid.set_cell(dx, dy, CellType.FLOOR)

        # 4. Multiple Realistic Building Exits
        # West Wing Exit (col 0)
        west_exits = [(0, 15), (0, 16)]
        # East Wing Exit (col 29)
        east_exits = [(width - 1, 15), (width - 1, 16)]
        # South Main Entrance / Egress (row height-1)
        south_exits = [(13, height - 1), (14, height - 1), (15, height - 1), (16, height - 1)]
        # North Plaza Exit (row 0, top of Room B)
        north_exits = [(14, 0), (15, 0)]

        all_exits = west_exits + east_exits + south_exits + north_exits
        for ex, ey in all_exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        # 5. Assemble Building and Room Metadata
        building = cls(grid, name="University Academic & Student Center")
        building.exits = all_exits

        building.add_room(Room(
            name="Room A (West Wing)",
            x1=1, y1=1, x2=8, y2=11,
            doorways=room_a_doors
        ))
        building.add_room(Room(
            name="Room B (Central Hall)",
            x1=10, y1=1, x2=19, y2=11,
            doorways=room_b_doors
        ))
        building.add_room(Room(
            name="Room C (East Wing)",
            x1=21, y1=1, x2=28, y2=11,
            doorways=room_c_doors
        ))
        building.add_room(Room(
            name="Main Concourse Corridor",
            x1=1, y1=13, x2=28, y2=18,
            doorways=[]
        ))

        return building
