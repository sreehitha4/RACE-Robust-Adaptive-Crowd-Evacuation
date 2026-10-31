"""Architectural building complex with realistic layout, zoning colors, and obstacles.

Models an expansive university student center and academic concourse:
  - West Wing: Lecture Theater & Classrooms (cool slate)
  - Central Atrium: Grand Concourse with pillars & seating (warm quartz)
  - East Wing: Library & Study Lounge (soft mint)
  - 4 Cardinal Exits: South Grand Entrance, North Plaza, West Courtyard, East Garden
  - Real architectural obstacles (Information Kiosk, Study Pods, Planter Lounges, Lecture Desks)
  - Dynamic interactive hazards (fire, smoke, temporary barriers)
"""

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional, Set, Tuple
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
    floor_color: Tuple[int, int, int] = (238, 242, 246)

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

    FLOOR_PLAN_CAMPUS = "University Campus Complex"
    FLOOR_PLAN_OFFICE = "Corporate Office & Research Suites"
    FLOOR_PLAN_TERMINAL = "Airport Transit Terminal"
    FLOOR_PLAN_PROCEDURAL = "Procedural Unseen Floor Plan"

    AVAILABLE_PLANS = [
        FLOOR_PLAN_CAMPUS,
        FLOOR_PLAN_OFFICE,
        FLOOR_PLAN_TERMINAL,
        FLOOR_PLAN_PROCEDURAL
    ]

    def __init__(self, grid: Grid, name: str = "University Student Center & Concourse", plan_type: str = FLOOR_PLAN_CAMPUS) -> None:
        self.grid: Grid = grid
        self.name: str = name
        self.plan_type: str = plan_type
        self.rooms: Dict[str, Room] = {}
        self.exits: List[Tuple[int, int]] = []
        self.pillars: Set[Tuple[int, int]] = set()
        self.obstacles: Dict[Tuple[int, int], str] = {}  # (x, y) -> type: "KIOSK", "BENCH", "PLANTER", "DESK"
        self.doorways: Set[Tuple[int, int]] = set()
        self.hazards: Set[Tuple[int, int]] = set()

    def add_room(self, room: Room) -> None:
        self.rooms[room.name] = room
        for d in room.doorways:
            self.doorways.add(d)

    def get_room_at(self, gx: float, gy: float) -> Optional[Room]:
        """Find the room enclosing continuous coordinate (gx, gy)."""
        for room in self.rooms.values():
            if room.contains(gx, gy):
                return room
        return None

    def add_obstacle(self, x: int, y: int, obstacle_type: str = "BENCH") -> None:
        """Register a permanent architectural obstacle."""
        self.obstacles[(x, y)] = obstacle_type
        self.grid.set_cell(x, y, CellType.WALL)

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
    def create_by_plan(cls, plan_type: str, width: int = 34, height: int = 22) -> "Building":
        """Factory method to construct any supported floor plan."""
        if plan_type == cls.FLOOR_PLAN_OFFICE:
            return cls.create_office_complex(width, height)
        elif plan_type == cls.FLOOR_PLAN_TERMINAL:
            return cls.create_transit_terminal(width, height)
        elif plan_type == cls.FLOOR_PLAN_PROCEDURAL:
            return cls.create_procedural_floor_plan(width, height)
        else:
            return cls.create_default(width, height)

    @classmethod
    def create_default(cls, width: int = 34, height: int = 22) -> "Building":
        """Floor Plan 1: University Student Center & Concourse with 4 realistic obstacles."""
        grid = Grid(width, height, default_cell=CellType.FLOOR)

        # Exterior Perimeter Boundary
        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        # Dividing Walls
        grid.fill_rect(10, 1, 10, 13, CellType.WALL)
        grid.fill_rect(23, 1, 23, 13, CellType.WALL)
        grid.fill_rect(1, 13, width - 2, 13, CellType.WALL)

        # Doorways
        room_a_doors = [(4, 13), (5, 13)]
        room_b_doors = [(16, 13), (17, 13)]
        room_c_doors = [(27, 13), (28, 13)]

        for dx, dy in room_a_doors + room_b_doors + room_c_doors:
            grid.set_cell(dx, dy, CellType.FLOOR)

        # Architectural Pillars
        pillars = {(14, 6), (19, 6), (14, 18), (19, 18)}
        for px, py in pillars:
            grid.set_cell(px, py, CellType.WALL)

        # Exits
        west_exits = [(0, 16), (0, 17)]
        east_exits = [(width - 1, 16), (width - 1, 17)]
        south_exits = [(15, height - 1), (16, height - 1), (17, height - 1), (18, height - 1)]
        north_exits = [(16, 0), (17, 0)]

        all_exits = west_exits + east_exits + south_exits + north_exits
        for ex, ey in all_exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        building = cls(grid, name="University Student Center & Concourse", plan_type=cls.FLOOR_PLAN_CAMPUS)
        building.exits = all_exits
        building.pillars = pillars

        # Add 4 Realistic Architectural Obstacles
        # 1. Central Information Kiosk (Concourse center)
        building.add_obstacle(16, 16, "KIOSK")
        building.add_obstacle(17, 16, "KIOSK")

        # 2. West Wing Lecture Desk Cluster
        building.add_obstacle(4, 3, "DESK")
        building.add_obstacle(5, 3, "DESK")

        # 3. East Wing Study Pod / Cubicle
        building.add_obstacle(26, 5, "BENCH")
        building.add_obstacle(27, 5, "BENCH")

        # 4. Concourse Architectural Green Planters (Flanking thoroughfare)
        building.add_obstacle(8, 17, "PLANTER")
        building.add_obstacle(9, 17, "PLANTER")
        building.add_obstacle(24, 17, "PLANTER")
        building.add_obstacle(25, 17, "PLANTER")

        building.add_room(Room(
            name="Room A (West Wing - Lecture Hall)",
            x1=1, y1=1, x2=9, y2=12,
            doorways=room_a_doors,
            floor_color=(230, 237, 246)
        ))
        building.add_room(Room(
            name="Room B (Central Atrium & Food Court)",
            x1=11, y1=1, x2=22, y2=12,
            doorways=room_b_doors,
            floor_color=(244, 242, 238)
        ))
        building.add_room(Room(
            name="Room C (East Wing - Library & Study)",
            x1=24, y1=1, x2=width - 2, y2=12,
            doorways=room_c_doors,
            floor_color=(232, 242, 238)
        ))
        building.add_room(Room(
            name="Main Concourse Corridor",
            x1=1, y1=14, x2=width - 2, y2=height - 2,
            doorways=[],
            floor_color=(240, 243, 248)
        ))
        return building

    @classmethod
    def create_office_complex(cls, width: int = 34, height: int = 22) -> "Building":
        """Floor Plan 2: Corporate Office & Research Suites with 4 Obstacles."""
        grid = Grid(width, height, default_cell=CellType.FLOOR)

        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        # Horizontal spine corridor walls: row 8 and row 13
        grid.fill_rect(1, 8, width - 2, 8, CellType.WALL)
        grid.fill_rect(1, 13, width - 2, 13, CellType.WALL)

        grid.fill_rect(11, 1, 11, 7, CellType.WALL)
        grid.fill_rect(22, 1, 22, 7, CellType.WALL)
        grid.fill_rect(11, 14, 11, 20, CellType.WALL)
        grid.fill_rect(22, 14, 22, 20, CellType.WALL)

        doors_top = [(5, 8), (6, 8), (16, 8), (17, 8), (27, 8), (28, 8)]
        doors_bottom = [(5, 13), (6, 13), (16, 13), (17, 13), (27, 13), (28, 13)]
        for dx, dy in doors_top + doors_bottom:
            grid.set_cell(dx, dy, CellType.FLOOR)

        west_exits = [(0, 10), (0, 11)]
        east_exits = [(width - 1, 10), (width - 1, 11)]
        south_exits = [(16, height - 1), (17, height - 1)]

        all_exits = west_exits + east_exits + south_exits
        for ex, ey in all_exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        building = cls(grid, name="Corporate Office & Research Suites", plan_type=cls.FLOOR_PLAN_OFFICE)
        building.exits = all_exits

        # 4 Office Obstacles
        building.add_obstacle(5, 4, "DESK")
        building.add_obstacle(16, 4, "DESK")
        building.add_obstacle(27, 4, "DESK")
        building.add_obstacle(16, 17, "BENCH")

        building.add_room(Room("Suite 101 (Executive Office)", 1, 1, 10, 7, doors_top[0:2], floor_color=(235, 238, 245)))
        building.add_room(Room("Suite 102 (R&D Engineering Lab)", 12, 1, 21, 7, doors_top[2:4], floor_color=(242, 238, 232)))
        building.add_room(Room("Suite 103 (Finance & Legal)", 23, 1, width - 2, 7, doors_top[4:6], floor_color=(234, 242, 238)))
        building.add_room(Room("Central Spine Corridor", 1, 9, width - 2, 12, [], floor_color=(245, 246, 250)))
        building.add_room(Room("Suite 201 (Team Collaboration)", 1, 14, 10, 20, doors_bottom[0:2], floor_color=(238, 244, 248)))
        building.add_room(Room("Suite 202 (Conference Center)", 12, 14, 21, 20, doors_bottom[2:4], floor_color=(246, 243, 238)))
        building.add_room(Room("Suite 203 (Customer Support Hub)", 23, 14, width - 2, 20, doors_bottom[4:6], floor_color=(235, 242, 240)))

        return building

    @classmethod
    def create_transit_terminal(cls, width: int = 34, height: int = 22) -> "Building":
        """Floor Plan 3: Airport Transit Terminal with Choke Points and Island Obstacles."""
        grid = Grid(width, height, default_cell=CellType.FLOOR)

        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        # Security screening partition wall
        grid.fill_rect(12, 1, 12, height - 2, CellType.WALL)
        security_gates = [(12, 10), (12, 11)]
        for gx, gy in security_gates:
            grid.set_cell(gx, gy, CellType.FLOOR)

        # Duty Free Island Wall
        grid.fill_rect(22, 7, 24, 14, CellType.WALL)

        west_exits = [(0, 10), (0, 11)]
        east_gates = [(width - 1, 5), (width - 1, 6), (width - 1, 15), (width - 1, 16)]
        south_tarmac = [(18, height - 1), (19, height - 1)]

        all_exits = west_exits + east_gates + south_tarmac
        for ex, ey in all_exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        building = cls(grid, name="Airport Transit Terminal", plan_type=cls.FLOOR_PLAN_TERMINAL)
        building.exits = all_exits

        # 4 Transit Obstacles
        building.add_obstacle(5, 7, "KIOSK")
        building.add_obstacle(5, 14, "KIOSK")
        building.add_obstacle(17, 7, "BENCH")
        building.add_obstacle(17, 14, "BENCH")

        building.add_room(Room("Ticketing & Check-in Hall", 1, 1, 11, height - 2, security_gates, floor_color=(236, 240, 248)))
        building.add_room(Room("Departure Concourse & Gates", 13, 1, width - 2, height - 2, [], floor_color=(245, 242, 238)))

        return building

    @classmethod
    def create_procedural_floor_plan(cls, width: int = 34, height: int = 22, seed: int = 777) -> "Building":
        """Floor Plan 4: Procedural Unseen Layout Generator with Obstacles."""
        grid = Grid(width, height, default_cell=CellType.FLOOR)
        rng = random.Random(seed)

        grid.fill_rect(0, 0, width - 1, 0, CellType.WALL)
        grid.fill_rect(0, height - 1, width - 1, height - 1, CellType.WALL)
        grid.fill_rect(0, 0, 0, height - 1, CellType.WALL)
        grid.fill_rect(width - 1, 0, width - 1, height - 1, CellType.WALL)

        split_x1 = 11
        split_x2 = 22
        grid.fill_rect(split_x1, 1, split_x1, height - 2, CellType.WALL)
        grid.fill_rect(split_x2, 1, split_x2, height - 2, CellType.WALL)

        split_y = 11
        grid.fill_rect(1, split_y, split_x1 - 1, split_y, CellType.WALL)
        grid.fill_rect(split_x2 + 1, split_y, width - 2, split_y, CellType.WALL)

        doorways = [
            (split_x1, 5), (split_x1, 6), (split_x1, 16), (split_x1, 17),
            (split_x2, 5), (split_x2, 6), (split_x2, 16), (split_x2, 17),
            (5, split_y), (6, split_y),
            (27, split_y), (28, split_y)
        ]
        for dx, dy in doorways:
            grid.set_cell(dx, dy, CellType.FLOOR)

        exits = [
            (0, 8), (0, 9),
            (width - 1, 8), (width - 1, 9),
            (16, height - 1), (17, height - 1),
            (16, 0), (17, 0)
        ]
        for ex, ey in exits:
            grid.set_cell(ex, ey, CellType.EXIT)

        building = cls(grid, name="Procedural Unseen Floor Plan", plan_type=cls.FLOOR_PLAN_PROCEDURAL)
        building.exits = exits

        # 4 Procedural Obstacles
        building.add_obstacle(5, 5, "PLANTER")
        building.add_obstacle(5, 17, "PLANTER")
        building.add_obstacle(28, 5, "BENCH")
        building.add_obstacle(28, 17, "BENCH")

        building.add_room(Room("Zone Alpha (Northwest)", 1, 1, split_x1 - 1, split_y - 1, [(5, split_y)], floor_color=(235, 240, 248)))
        building.add_room(Room("Zone Beta (Southwest)", 1, split_y + 1, split_x1 - 1, height - 2, [(5, split_y)], floor_color=(238, 244, 240)))
        building.add_room(Room("Central Atrium Corridor", split_x1 + 1, 1, split_x2 - 1, height - 2, [], floor_color=(245, 245, 248)))
        building.add_room(Room("Zone Gamma (Northeast)", split_x2 + 1, 1, width - 2, split_y - 1, [(27, split_y)], floor_color=(246, 240, 235)))
        building.add_room(Room("Zone Delta (Southeast)", split_x2 + 1, split_y + 1, width - 2, height - 2, [(27, split_y)], floor_color=(242, 244, 246)))

        return building
