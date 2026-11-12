import type { Agent, Environment, Frame } from "./contract.ts";

const TRAIL_SECONDS = 6;

/** Everything the canvas and the stats panel read. Lives outside React so the 60 fps loop never re-renders components. */
export class RunStore {
  env: Environment | null = null;
  frame: Frame | null = null;
  trails = new Map<Agent["id"], [number, number, number][]>(); // [x, y, t]
  series: [number, number][] = []; // [simulation_time, evacuated] for the evacuation curve
  private prev = new Map<Agent["id"], Agent>();
  private at = 0; // performance.now() when the latest frame arrived
  private gap = 0; // ms between the last two frames, used to interpolate

  setEnvironment(env: Environment) {
    this.env = env;
    this.clear();
  }

  clear() {
    this.frame = null;
    this.prev.clear();
    this.trails.clear();
    this.series = [];
  }

  push(f: Frame, now: number) {
    if (this.frame && f.simulation_time < this.frame.simulation_time) this.clear(); // a reset we were not told about
    this.prev = new Map(this.frame?.agents.map((a) => [a.id, a]) ?? []);
    this.gap = this.frame ? Math.min(Math.max(now - this.at, 16), 250) : 0;
    this.at = now;
    this.frame = f;

    const t = f.simulation_time;
    const seen = new Set<Agent["id"]>();
    for (const a of f.agents) {
      if (a.state === "evacuated") continue;
      seen.add(a.id);
      const trail = this.trails.get(a.id) ?? [];
      trail.push([a.x, a.y, t]);
      while (trail[0][2] < t - TRAIL_SECONDS) trail.shift();
      this.trails.set(a.id, trail);
    }
    for (const id of this.trails.keys()) if (!seen.has(id)) this.trails.delete(id);

    const last = this.series.at(-1);
    if (!last || last[1] !== f.evacuated || t - last[0] >= 0.5) this.series.push([t, f.evacuated]);
  }

  /** Agents with positions interpolated between the last two frames, so 10 Hz data animates at display rate. */
  agentsAt(now: number): Agent[] {
    if (!this.frame) return [];
    const live = this.frame.agents.filter((a) => a.state !== "evacuated");
    const k = this.gap ? Math.min(1, Math.max(0, (now - this.at) / this.gap)) : 1;
    if (k === 1) return live;
    return live.map((a) => {
      const p = this.prev.get(a.id);
      return p ? { ...a, x: p.x + (a.x - p.x) * k, y: p.y + (a.y - p.y) * k } : a;
    });
  }

  /** Simulation time at which `share` of all agents had evacuated (T50, T90), if reached. */
  timeTo(share: number): number | undefined {
    const total = this.frame?.total_agents ?? 0;
    return total ? this.series.find(([, e]) => e >= share * total)?.[0] : undefined;
  }

  /** Agents leaving per second over the last `window` seconds of simulation time. */
  flow(window = 5): number {
    const last = this.series.at(-1);
    if (!last) return 0;
    const from = this.series.findLast(([t]) => t <= last[0] - window) ?? this.series[0];
    return last[0] > from[0] ? (last[1] - from[1]) / (last[0] - from[0]) : 0;
  }
}
