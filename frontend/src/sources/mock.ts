// Synthetic in-browser simulation so the UI can be built and demoed before the backend exists.
// It is deliberately simple (flow-field navigation + social-force separation) and is always
// labelled as mock data in the UI. It is NOT the RACE simulation engine (workstream 2).
import type { Agent, Environment, Frame, Point } from "../contract.ts";
import type { Sink, Source } from "./types.ts";

const W = 40;
const H = 24;
const CELL = 0.25; // flow-field resolution, metres
const RADIUS = 0.25; // agent body radius
const CLEAR = 0.35; // how far agent centres stay from walls and obstacles
const TAU = 0.5; // seconds to relax towards the desired velocity
const PUSH = 2.5; // social-force strength, m/s²
const RANGE = 0.25; // social-force fall-off, metres
export const DT = 0.1; // seconds per published frame

const rect = (x0: number, y0: number, x1: number, y1: number): Point[] => [
  [x0, y0], [x1, y0], [x1, y1], [x0, y1],
];

export const LAYOUT: Environment = {
  type: "environment",
  width: W,
  height: H,
  walls: [
    [[0, 10], [0, 0], [40, 0], [40, 14]],
    [[40, 16.5], [40, 24], [21, 24]],
    [[18.5, 24], [0, 24], [0, 12.5]],
    [[14, 0], [14, 4]],
    [[14, 6.5], [14, 15]],
    [[14, 17.5], [14, 24]],
    [[28, 0], [28, 3]],
    [[28, 5.5], [28, 10], [34, 10]],
  ],
  obstacles: [
    rect(3.5, 3.5, 7, 5.5),
    rect(3.5, 17, 7, 19.5),
    rect(8, 9.5, 10, 14),
    rect(19.5, 7.5, 20.5, 8.5),
    rect(24.5, 7.5, 25.5, 8.5),
    rect(19.5, 15.5, 20.5, 16.5),
    rect(24.5, 15.5, 25.5, 16.5),
    rect(31, 15, 35, 19),
    rect(32, 4, 35, 6.5),
  ],
  exits: [
    { id: "W", polygon: rect(0, 10, 0.6, 12.5) },
    { id: "E", polygon: rect(39.4, 14, 40, 16.5) },
    { id: "N", polygon: rect(18.5, 23.4, 21, 24) },
  ],
};

export function insidePolygon(x: number, y: number, poly: Point[]): boolean {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

function segmentDistance(x: number, y: number, [ax, ay]: Point, [bx, by]: Point): number {
  const dx = bx - ax;
  const dy = by - ay;
  const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(x - ax - t * dx, y - ay - t * dy);
}

function nearLine(x: number, y: number, line: Point[], closed: boolean, r: number): boolean {
  const n = closed ? line.length : line.length - 1;
  for (let i = 0; i < n; i++) if (segmentDistance(x, y, line[i], line[(i + 1) % line.length]) < r) return true;
  return false;
}

// Deterministic RNG so tests (and seeded runs) are reproducible.
function mulberry32(seed: number) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const COLS = Math.round(W / CELL);
const ROWS = Math.round(H / CELL);
const NEIGHBOURS: [number, number, number][] = [
  [1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1],
  [1, 1, Math.SQRT2], [1, -1, Math.SQRT2], [-1, 1, Math.SQRT2], [-1, -1, Math.SQRT2],
];

// The floor plan is fixed, so blocked cells and the distance-to-exit field are computed once.
const blocked = new Uint8Array(COLS * ROWS);
const distance = new Float64Array(COLS * ROWS).fill(Infinity);
let walkableArea = 0;
{
  const goals: number[] = [];
  for (let j = 0; j < ROWS; j++) {
    for (let i = 0; i < COLS; i++) {
      const x = (i + 0.5) * CELL;
      const y = (j + 0.5) * CELL;
      const k = j * COLS + i;
      blocked[k] = Number(
        LAYOUT.walls.some((w) => nearLine(x, y, w, false, CLEAR)) ||
          LAYOUT.obstacles.some((o) => insidePolygon(x, y, o) || nearLine(x, y, o, true, CLEAR)),
      );
      if (blocked[k]) continue;
      walkableArea += CELL * CELL;
      if (LAYOUT.exits.some((e) => insidePolygon(x, y, e.polygon))) {
        distance[k] = 0;
        goals.push(k);
      }
    }
  }
  // Dijkstra from every exit cell. A sorted queue is plenty for ~15k cells computed once.
  const queue = goals.map((k) => [0, k]);
  while (queue.length) {
    const [d, k] = queue.shift()!;
    if (d > distance[k]) continue;
    const i = k % COLS;
    const j = (k - i) / COLS;
    for (const [di, dj, len] of NEIGHBOURS) {
      const ni = i + di;
      const nj = j + dj;
      if (ni < 0 || nj < 0 || ni >= COLS || nj >= ROWS) continue;
      const n = nj * COLS + ni;
      // no squeezing diagonally past a blocked corner
      if (blocked[n] || blocked[j * COLS + ni] || blocked[nj * COLS + i]) continue;
      const nd = d + len * CELL;
      if (nd < distance[n]) {
        distance[n] = nd;
        let lo = 0;
        let hi = queue.length;
        while (lo < hi) {
          const mid = (lo + hi) >> 1;
          if (queue[mid][0] < nd) lo = mid + 1;
          else hi = mid;
        }
        queue.splice(lo, 0, [nd, n]);
      }
    }
  }
}

function cellOf(x: number, y: number): number {
  const i = Math.floor(x / CELL);
  const j = Math.floor(y / CELL);
  return i < 0 || j < 0 || i >= COLS || j >= ROWS ? -1 : j * COLS + i;
}

export function isBlocked(x: number, y: number): boolean {
  const k = cellOf(x, y);
  return k < 0 || blocked[k] === 1;
}

interface Walker extends Agent {
  speed: number; // preferred walking speed
}

export class MockSim {
  time = 0;
  evacuated = 0;
  readonly total: number;
  agents: Walker[] = [];

  constructor(count: number, seed: number) {
    const rand = mulberry32(seed);
    let id = 1;
    for (let tries = 0; this.agents.length < count && tries < count * 200; tries++) {
      const x = rand() * W;
      const y = rand() * H;
      const k = cellOf(x, y);
      if (k < 0 || blocked[k] || distance[k] < 3 || !Number.isFinite(distance[k])) continue;
      if (this.agents.some((a) => Math.hypot(a.x - x, a.y - y) < 2.4 * RADIUS)) continue;
      // preferred speeds around the commonly cited 1.34 m/s pedestrian mean
      this.agents.push({ id: id++, x, y, vx: 0, vy: 0, state: "walking", speed: 1.0 + rand() * 0.7 });
    }
    this.total = this.agents.length;
  }

  get done(): boolean {
    return this.agents.length === 0;
  }

  step(dt: number) {
    const n = this.agents.length;
    const fx = new Float64Array(n);
    const fy = new Float64Array(n);
    for (let a = 0; a < n; a++) {
      const p = this.agents[a];
      // desired heading: slope-weighted average of every downhill neighbour in the distance field
      const k = cellOf(p.x, p.y);
      const i = k % COLS;
      const j = (k - i) / COLS;
      let gx = 0;
      let gy = 0;
      for (const [di, dj, len] of NEIGHBOURS) {
        const ni = i + di;
        const nj = j + dj;
        if (ni < 0 || nj < 0 || ni >= COLS || nj >= ROWS) continue;
        // capped so a cell the field never reached (Infinity) still points somewhere sensible
        const drop = Math.min(distance[k] - distance[nj * COLS + ni], 2 * CELL);
        if (drop > 0) {
          gx += (di / len) * (drop / len);
          gy += (dj / len) * (drop / len);
        }
      }
      const g = Math.hypot(gx, gy) || 1;
      fx[a] += ((gx / g) * p.speed - p.vx) / TAU;
      fy[a] += ((gy / g) * p.speed - p.vy) / TAU;
      for (let b = a + 1; b < n; b++) {
        const q = this.agents[b];
        const dx = p.x - q.x;
        const dy = p.y - q.y;
        const d = Math.hypot(dx, dy);
        if (d > 2 || d === 0) continue;
        const f = PUSH * Math.exp((2 * RADIUS - d) / RANGE);
        fx[a] += (dx / d) * f;
        fy[a] += (dy / d) * f;
        fx[b] -= (dx / d) * f;
        fy[b] -= (dy / d) * f;
      }
    }
    for (let a = 0; a < n; a++) {
      const p = this.agents[a];
      p.vx += fx[a] * dt;
      p.vy += fy[a] * dt;
      const v = Math.hypot(p.vx, p.vy);
      const max = 1.3 * p.speed;
      if (v > max) {
        p.vx *= max / v;
        p.vy *= max / v;
      }
      // slide along walls instead of passing through them
      const nx = p.x + p.vx * dt;
      const ny = p.y + p.vy * dt;
      if (!isBlocked(nx, ny)) {
        p.x = nx;
        p.y = ny;
      } else if (!isBlocked(nx, p.y)) {
        p.x = nx;
        p.vy = 0;
      } else if (!isBlocked(p.x, ny)) {
        p.y = ny;
        p.vx = 0;
      } else {
        p.vx = 0;
        p.vy = 0;
      }
      // slower than 0.5 m/s counts as held up by the crowd
      p.state = Math.hypot(p.vx, p.vy) < 0.5 ? "waiting" : "walking";
    }
    const before = this.agents.length;
    this.agents = this.agents.filter((p) => !LAYOUT.exits.some((e) => insidePolygon(p.x, p.y, e.polygon)));
    this.evacuated += before - this.agents.length;
    this.time += dt;
  }

  frame(): Frame {
    return {
      type: "frame",
      simulation_time: Math.round(this.time * 1000) / 1000,
      total_agents: this.total,
      evacuated: this.evacuated,
      density: this.agents.length / walkableArea,
      prediction_model: "constant-velocity (mock)",
      agents: this.agents.map(({ id, x, y, vx, vy, state }) => ({
        id, x, y, vx, vy, state,
        // 12 steps x 0.4 s, the usual ETH-UCY prediction horizon
        predicted: Array.from({ length: 12 }, (_, s): Point => [x + vx * 0.4 * (s + 1), y + vy * 0.4 * (s + 1)]),
      })),
    };
  }
}

export function createMockSource(sink: Sink, count = 200): Source {
  let sim = new MockSim(count, Date.now());
  let timer: ReturnType<typeof setInterval> | undefined;
  const stop = () => {
    clearInterval(timer);
    timer = undefined;
  };
  const publish = () => {
    sink.environment(LAYOUT);
    sink.frame(sim.frame());
  };
  sink.status("Mock data · synthetic, in-browser", "warn");
  publish();
  return {
    async start() {
      if (sim.done) {
        sim = new MockSim(count, Date.now());
        publish();
      }
      timer ??= setInterval(() => {
        // two half-steps per frame keep the social force stable at 10 Hz
        sim.step(DT / 2);
        sim.step(DT / 2);
        sink.frame(sim.frame());
        if (sim.done) {
          stop();
          sink.stopped();
        }
      }, DT * 1000);
    },
    async pause() {
      stop();
    },
    async reset() {
      stop();
      sim = new MockSim(count, Date.now());
      publish();
    },
    close: stop,
  };
}
