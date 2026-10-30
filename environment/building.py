"""Architectural building complex with realistic layout, pillars, and multiple exits.

Models an expansive university student center and academic concourse:
  - West Wing: Lecture Theater & Classrooms
  - Central Atrium: Grand Concourse with architectural pillars & seating
  - East Wing: Library & Study Lounge
  - 4 Cardinal Exits: South Grand Entrance, North Plaza, West Courtyard, East Garden
  - Dynamic interactive hazards (fire, smoke, temporary barriers)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
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

    def contains(self, x: float, y: float) -> bool:
        """Check if a coordinate (x, y) is inside this room."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def get_interior_cells(self) -> List[Tuple[int, int]]:
        """Return all grid coordinates enclosed within this room."""
        cells: List[Tuple[int, int]] = []
        for y in range(self.y1, self.y2 + 1):
            for x in range(self.x1, self.x2 + 1):
                cells.append((x, y))
        return cells


class Building:
    """Represents an architectural complex with rooms, pillars, and multiple exits."""

    def __init__(self, grid: Grid, name: str = "University Student Center & Concourse") -> None:
        self.grid: Grid = grid
        self.name: str = name
        self.rooms: Dict[str, Room] = {}
        self.exits: List[Tuple[int, int]] = []
        self.pillars: Set[Tuple[int, int]] = set()
        self.hazards: Set[Tuple[int, int]] = set()  # Dynamic fire/smoke hazard cells

    def add_room(self, room: Room) -> None:
        self.rooms[room.name] = room

    def add_hazard(self, x: int, y: int) -> bool:
        """Dynamically place a fire / hazard obstacle."""
        if not self.grid.is_inside(x, y) or self.grid.is_wall(x, y):
            return False
        self.hazards.add((x, y))
        self.grid.set_cell(x, y, CellType.WALL)
        return True

    def remove_hazard(self, x: int, y: int) -> bool:
        """Remove a hazard from the floor."""
        if (x, y) in self.hazards:
            self.hazards.remove((x, y))
            self.grid.set_cell(x, y, CellType.FLOOR)
            return True
        return False

    @classmethod
    def create_default(cls, width: int = 34, height: int = 22) -> "Building":
        """Construct a realistic campus complex with pillars, corridors, and 4 exits."""
        grid = Grid(width, height, default_cell=CellType.FLOOR)

        # 1. Perimeter Exterior Boundary
        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        # 2. Interior Walls
        # Vertical wall separating West Wing and Central Atrium
        grid.fill_rect(10, 1, 10, 13, CellType.WALL)
        # Vertical wall separating Central Atrium and East Wing
        grid.fill_rect(23, 1, 23, 13, CellType.WALL)
        # Horizontal concourse divider
        grid.fill_rect(1, 13, width - 2, 13, CellType.WALL)

        # 3. Wide Architectural Doorways (2 cells wide for natural crowd flow)
        room_a_doors = [(4, 13), (5, 13)]
        room_b_doors = [(16, 13), (17, 13)]
        room_c_doors = [(27, 13), (28, 13)]

        for dx, dy in room_a_doors + room_b_doors + room_c_doors:
            grid.set_cell(dx, dy, CellType.FLOOR)

        # 4. Central Atrium Architectural Pillars (structural pillars people glide around!)
        pillars = {
            (14, 6), (19, 6),
            (14, 17), (19, 17)
        }
        for px, py in pillars:
            grid.set_cell(px, py, CellType.WALL)

        # 5. Four Distinct, Prominent Exits across All Cardinal Directions
        # West Wing Exit (West boundary, row 16-17)
        west_exits = [(0, 16), (0, 17)]
        # East Wing Exit (East boundary, row 16-17)
        east_exits = [(width - 1, 16), (width - 1, 17)]
        # South Grand Entrance / Egress (South boundary, 4 cells wide: cols 15..18)
        south_exits = [(15, height - 1), (16, height - 1), (17, height - 1), (18, height - 1)]
        # North Plaza Exit (North boundary, 2 cells wide: cols 16..17)
        north_exits = [(16, 0), (17, 0)]

        all_exits = west_exits + east_exits + south_exits + north_exits
        for ex, ey in all_exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        # 6. Metadata Registration
        building = cls(grid, name="University Student Center & Concourse")
        building.exits = all_exits
        building.pillars = pillars

        building.add_room(Room(
            name="Room A (West Wing - Lecture Hall)",
            x1=1, y1=1, x2=9, y2=12,
            doorways=room_a_doors
        ))
        building.add_room(Room(
            name="Room B (Central Atrium & Food Court)",
            x1=11, y1=1, x2=22, y2=12,
            doorways=room_b_doors
        ))
        building.add_room(Room(
            name="Room C (East Wing - Library & Study)",
            x1=24, y1=1, x2=width - 2, y2=12,
            doorways=room_c_doors
        ))
        building.add_room(Room(
            name="Main Concourse Corridor",
            x1=1, y1=14, x2=width - 2, y2=height - 2,
            doorways=[]
        ))

        return building
