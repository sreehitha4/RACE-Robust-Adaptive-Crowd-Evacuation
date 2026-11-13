"""Point quadtree for local-neighbour queries in dense pedestrian simulations."""
from dataclasses import dataclass, field

@dataclass
class _Node:
    x: float
    y: float
    half: float
    capacity: int = 12
    depth: int = 0
    points: list = field(default_factory=list)
    children: list | None = None

    def contains(self, x, y):
        return self.x-self.half <= x <= self.x+self.half and self.y-self.half <= y <= self.y+self.half

    def insert(self, item):
        x, y = float(item.position[0]), float(item.position[1])
        if not self.contains(x, y):
            return False
        if self.children is None and (len(self.points) < self.capacity or self.depth >= 16):
            self.points.append(item)
            return True
        if self.children is None:
            self._split()
            old, self.points = self.points, []
            for point in old:
                self._insert_child(point)
        return self._insert_child(item)

    def _split(self):
        h = self.half / 2
        self.children = [
            _Node(self.x-h, self.y-h, h, self.capacity, self.depth+1),
            _Node(self.x+h, self.y-h, h, self.capacity, self.depth+1),
            _Node(self.x-h, self.y+h, h, self.capacity, self.depth+1),
            _Node(self.x+h, self.y+h, h, self.capacity, self.depth+1),
        ]

    def _insert_child(self, item):
        for child in self.children:
            if child.insert(item):
                return True
        return False

    def query(self, x, y, radius, out):
        if x+radius < self.x-self.half or x-radius > self.x+self.half or y+radius < self.y-self.half or y-radius > self.y+self.half:
            return
        if self.children is None:
            r2 = radius*radius
            for item in self.points:
                dx, dy = float(item.position[0])-x, float(item.position[1])-y
                if dx*dx+dy*dy <= r2:
                    out.append(item)
        else:
            for child in self.children:
                child.query(x, y, radius, out)

class QuadTree:
    def __init__(self, items=(), bounds=None, capacity=12):
        items = list(items)
        if bounds is None:
            if items:
                xs = [float(a.position[0]) for a in items]
                ys = [float(a.position[1]) for a in items]
                cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
                half = max(max(xs)-min(xs), max(ys)-min(ys), 1.0)/2 + 1e-6
            else:
                cx = cy = 0.0; half = 1.0
        else:
            min_x, min_y, max_x, max_y = bounds
            cx, cy = (min_x+max_x)/2, (min_y+max_y)/2
            half = max(max_x-min_x, max_y-min_y)/2 + 1e-6
        self.root = _Node(cx, cy, half, capacity)
        for item in items:
            self.root.insert(item)

    def query_radius(self, x, y, radius):
        found = []
        self.root.query(float(x), float(y), max(0.0, float(radius)), found)
        return found
