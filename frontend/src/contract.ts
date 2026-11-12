// RACE wire contract: the only shapes the frontend accepts. Mirrors CONTRACT.md.
// Units are metres and seconds. Origin is bottom-left, x points right, y points up
// (the same convention as Shapely and ETH-UCY world coordinates).

export type Point = [number, number];

/** Static floor plan. Sent once on connect and again after every reset. */
export interface Environment {
  type: "environment";
  width: number;
  height: number;
  walls: Point[][]; // polylines (Shapely LineString coords)
  obstacles: Point[][]; // polygons (Shapely Polygon exterior coords)
  exits: { id: string | number; polygon: Point[] }[];
}

export interface Agent {
  id: string | number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  state: string; // "walking" | "waiting" | "evacuated" are styled; anything else is drawn neutral
  predicted?: Point[]; // future positions from the trajectory model, nearest first
}

/** One simulation update. Streamed at ~10 Hz while running. */
export interface Frame {
  type: "frame";
  simulation_time: number;
  agents: Agent[];
  total_agents: number;
  evacuated: number;
  density?: number; // agents per m² of walkable floor
  prediction_model?: string; // shown next to predicted paths, e.g. "lstm" or "constant-velocity"
}

export type Message = Environment | Frame;

function fail(path: string, want: string, got: unknown): never {
  const shown = JSON.stringify(got)?.slice(0, 60) ?? String(got);
  throw new Error(`${path} should be ${want}, got ${shown}`);
}

function obj(v: unknown, path: string): Record<string, unknown> {
  if (typeof v !== "object" || v === null || Array.isArray(v)) fail(path, "an object", v);
  return v as Record<string, unknown>;
}

function arr(v: unknown, path: string): unknown[] {
  if (!Array.isArray(v)) fail(path, "an array", v);
  return v;
}

function num(v: unknown, path: string) {
  if (typeof v !== "number" || !Number.isFinite(v)) fail(path, "a finite number", v);
}

function points(v: unknown, path: string, min: number) {
  const a = arr(v, path);
  if (a.length < min) fail(path, `at least ${min} [x, y] points`, v);
  a.forEach((p, i) => {
    const q = arr(p, `${path}[${i}]`);
    num(q[0], `${path}[${i}][0]`);
    num(q[1], `${path}[${i}][1]`);
  });
}

function id(v: unknown, path: string) {
  if (typeof v !== "number" && typeof v !== "string") fail(path, "a number or string", v);
}

/** Validates an incoming message and returns it unchanged; throws a readable error naming the bad field. */
export function parseMessage(raw: unknown, path = "message"): Message {
  const m = obj(raw, path);
  if (m.type === "environment") {
    num(m.width, `${path}.width`);
    num(m.height, `${path}.height`);
    arr(m.walls, `${path}.walls`).forEach((w, i) => points(w, `${path}.walls[${i}]`, 2));
    arr(m.obstacles, `${path}.obstacles`).forEach((o, i) => points(o, `${path}.obstacles[${i}]`, 3));
    arr(m.exits, `${path}.exits`).forEach((e, i) => {
      const x = obj(e, `${path}.exits[${i}]`);
      id(x.id, `${path}.exits[${i}].id`);
      points(x.polygon, `${path}.exits[${i}].polygon`, 3);
    });
    return m as unknown as Environment;
  }
  if (m.type === "frame") {
    num(m.simulation_time, `${path}.simulation_time`);
    num(m.total_agents, `${path}.total_agents`);
    num(m.evacuated, `${path}.evacuated`);
    if (m.density !== undefined) num(m.density, `${path}.density`);
    arr(m.agents, `${path}.agents`).forEach((a, i) => {
      const p = `${path}.agents[${i}]`;
      const g = obj(a, p);
      id(g.id, `${p}.id`);
      for (const k of ["x", "y", "vx", "vy"]) num(g[k], `${p}.${k}`);
      if (typeof g.state !== "string") fail(`${p}.state`, "a string", g.state);
      if (g.predicted !== undefined) points(g.predicted, `${p}.predicted`, 0);
    });
    return m as unknown as Frame;
  }
  return fail(`${path}.type`, `"environment" or "frame"`, m.type);
}
