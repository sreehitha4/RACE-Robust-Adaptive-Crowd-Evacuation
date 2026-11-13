from dataclasses import dataclass
from shapely.geometry import Point, Polygon, box
import heapq
import math

@dataclass(frozen=True)
class Exit:
    id: str
    x: float
    y: float

class Environment:
    """Rectangular indoor floor plan with polygon obstacles and two exits."""
    def __init__(self, width=20.0, height=14.0, obstacles=None, exits=None):
        self.width, self.height = float(width), float(height)
        self.bounds = box(0, 0, self.width, self.height)
        self.obstacles = [Polygon(p) for p in (obstacles or [
            [(7.0, 3.0), (8.3, 3.0), (8.3, 8.0), (7.0, 8.0)],
            [(12.0, 6.0), (13.0, 6.0), (13.0, 11.0), (12.0, 11.0)]
        ])]
        self.exits = exits or [Exit("exit_west", 0.35, self.height/2), Exit("exit_east", self.width-0.35, self.height/2)]

    def is_walkable(self, x, y, radius=0.0, clearance=0.0):
        r = max(0.0, radius + clearance)
        if x-r < 0 or y-r < 0 or x+r > self.width or y+r > self.height:
            return False
        footprint = Point(float(x), float(y)).buffer(r) if r else Point(float(x), float(y))
        return not any(poly.intersects(footprint) for poly in self.obstacles)

    def nearest_exit(self, position):
        return min(self.exits, key=lambda e: (e.x-position[0])**2 + (e.y-position[1])**2)

    def find_path(self, start, goal, radius=0.22, clearance=0.12, cell=0.35):
        """A* grid route around obstacles; returns waypoints in world coordinates."""
        def to_cell(p): return (int(round(float(p[0])/cell)), int(round(float(p[1])/cell)))
        def to_world(c): return (c[0]*cell, c[1]*cell)
        start_c, goal_c = to_cell(start), to_cell(goal)
        max_x, max_y = int(self.width/cell), int(self.height/cell)
        def free(c):
            x,y=to_world(c)
            return 0 <= c[0] <= max_x and 0 <= c[1] <= max_y and self.is_walkable(x,y,radius,clearance)
        def nearest_free(c):
            if free(c): return c
            for r in range(1,20):
                candidates=[]
                for dx in range(-r,r+1):
                    for dy in range(-r,r+1):
                        if max(abs(dx),abs(dy))==r and free((c[0]+dx,c[1]+dy)):
                            candidates.append((c[0]+dx,c[1]+dy))
                if candidates: return min(candidates,key=lambda q:(q[0]-c[0])**2+(q[1]-c[1])**2)
            return None
        start_c, goal_c = nearest_free(start_c), nearest_free(goal_c)
        if start_c is None or goal_c is None: return [tuple(goal)]
        directions=[(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        def h(c): return math.hypot(c[0]-goal_c[0],c[1]-goal_c[1])
        frontier=[(h(start_c),0.0,start_c)]
        came={}; cost={start_c:0.0}; found=False
        while frontier:
            _,g,current=heapq.heappop(frontier)
            if current==goal_c: found=True; break
            if g>cost.get(current,float('inf')): continue
            for dx,dy in directions:
                nxt=(current[0]+dx,current[1]+dy)
                if not free(nxt): continue
                step=math.sqrt(2) if dx and dy else 1.0
                ng=g+step
                if ng<cost.get(nxt,float('inf')):
                    cost[nxt]=ng; came[nxt]=current
                    heapq.heappush(frontier,(ng+h(nxt),ng,nxt))
        if not found: return [tuple(goal)]
        cells=[goal_c]
        while cells[-1]!=start_c: cells.append(came[cells[-1]])
        cells.reverse()
        points=[to_world(c) for c in cells[1:]]
        if not points or math.dist(points[-1],goal)>cell: points.append(tuple(goal))
        # Line-of-sight pruning only when the entire segment clears obstacles.
        def segment_clear(a, b):
            distance = math.dist(a, b)
            samples = max(2, int(math.ceil(distance / (cell * 0.2))))
            for k in range(samples + 1):
                t = k / samples
                x = a[0] + (b[0] - a[0]) * t
                y = a[1] + (b[1] - a[1]) * t
                if not self.is_walkable(x, y, radius, clearance): return False
            return True
        compact=[]; anchor=tuple(start); i=0
        while i<len(points):
            j=len(points)-1
            while j>i and not segment_clear(anchor, points[j]): j-=1
            compact.append(points[j]); anchor=points[j]; i=j+1
        return compact

    def to_dict(self):
        return {"width": self.width, "height": self.height,
                "obstacles": [[list(c) for c in list(p.exterior.coords)[:-1]] for p in self.obstacles],
                "exits": [e.__dict__ for e in self.exits]}
