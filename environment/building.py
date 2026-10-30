"""Building layout and architectural environment definition.

Defines rooms, corridors, walls, doorways, and emergency exits,
ensuring all walkable areas have unobstructed connectivity to exits.
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

    def __init__(self, grid: Grid, name: str = "Standard Evacuation Facility") -> None:
        self.grid: Grid = grid
        self.name: str = name
        self.rooms: Dict[str, Room] = {}
        self.exits: List[Tuple[int, int]] = []

    def add_room(self, room: Room) -> None:
        """Register a room in the building."""
        self.rooms[room.name] = room

    @classmethod
    def create_default(cls, width: int = 30, height: int = 20) -> "Building":
        """Construct the standard benchmark layout.

        Architecture:
          - Dimensions: 30 columns x 20 rows.
          - Perimeter: Solid exterior walls with exit openings.
          - Room A (West Room): cols 1..8, rows 1..11.
          - Room B (Center Hall): cols 10..19, rows 1..11.
          - Room C (East Room): cols 21..28, rows 1..11.
          - Dividing Walls:
              * Vertical wall separating Room A and B: col 9, rows 1..12
              * Vertical wall separating Room B and C: col 20, rows 1..12
              * Horizontal wall separating rooms from corridor: row 12, cols 1..28
          - Doorways (2 cells wide for smooth flow):
              * Room A doorway: (4, 12), (5, 12)
              * Room B doorway: (14, 12), (15, 12)
              * Room C doorway: (24, 12), (25, 12)
          - Main Connecting Corridor: cols 1..28, rows 13..18.
          - Emergency Exits:
              * Exit 1 (West Exit): (0, 15) and (0, 16)
              * Exit 2 (East Exit): (29, 15) and (29, 16)
        """
        grid = Grid(width, height, default_cell=CellType.FLOOR)

        # 1. Exterior Perimeter Walls
        # Top and Bottom walls
        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        # Left and Right walls
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        # 2. Interior Dividing Walls
        # Vertical wall separating Room A and Room B
        grid.fill_rect(9, 1, 9, 12, CellType.WALL)
        # Vertical wall separating Room B and Room C
        grid.fill_rect(20, 1, 20, 12, CellType.WALL)
        # Horizontal wall separating all rooms from corridor
        grid.fill_rect(1, 12, width - 2, 12, CellType.WALL)

        # 3. Create Doorways (convert wall cells back to floor)
        room_a_doors = [(4, 12), (5, 12)]
        room_b_doors = [(14, 12), (15, 12)]
        room_c_doors = [(24, 12), (25, 12)]

        for dx, dy in room_a_doors + room_b_doors + room_c_doors:
            grid.set_cell(dx, dy, CellType.FLOOR)

        # 4. Emergency Exits (on exterior boundary of corridor)
        exits = [
            (0, 15), (0, 16),        # West Exit (2 cells wide)
            (width - 1, 15), (width - 1, 16)  # East Exit (2 cells wide)
        ]
        for ex, ey in exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        # 5. Assemble Building and Room Metadata
        building = cls(grid, name="University Science Complex")
        building.exits = exits

        building.add_room(Room(
            name="Room A (West Wing)",
            x1=1, y1=1, x2=8, y2=11,
            doorways=room_a_doors
        ))
        building.add_room(Room(
            name="Room B (Central Lecture Hall)",
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
