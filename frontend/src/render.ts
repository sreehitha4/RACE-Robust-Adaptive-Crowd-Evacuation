// Pure Canvas 2D drawing of one moment of a run. World units are metres, y up; the canvas is y down.
import type { Agent, Environment, Point } from "./contract.ts";
import type { RunStore } from "./store.ts";

export interface Layers {
  grid: boolean;
  trails: boolean;
  predictions: boolean;
  heatmap: boolean;
}

export interface View {
  scale: number; // px per metre
  ox: number;
  oy: number;
  height: number; // world height, for the y flip
}

// Warm "emergency signage" palette; keep in step with the tokens in styles.css.
export const COLORS = {
  bg: "#13110f",
  floor: "#1b1814",
  gridMinor: "rgba(255, 214, 170, 0.04)",
  gridMajor: "rgba(255, 214, 170, 0.09)",
  ink: "rgba(214, 196, 172, 0.7)",
  wall: "#f3e9da",
  obstacleFill: "rgba(196, 164, 124, 0.07)",
  obstacleLine: "rgba(220, 196, 164, 0.42)",
  exit: "#2fd47a",
  walking: "#f6e7cf",
  waiting: "#ff5a36",
  other: "#a89c8c",
  prediction: "#ffc533",
  selected: "#ff7a1a",
};

export const stateColor = (state: string) =>
  state === "walking" ? COLORS.walking : state === "waiting" ? COLORS.waiting : COLORS.other;

export function fitView(env: Environment, w: number, h: number): View {
  const pad = 36;
  const scale = Math.min((w - 2 * pad) / env.width, (h - 2 * pad) / env.height);
  return {
    scale,
    ox: (w - env.width * scale) / 2,
    oy: (h - env.height * scale) / 2,
    height: env.height,
  };
}

export const toScreen = (v: View, x: number, y: number): Point => [v.ox + x * v.scale, v.oy + (v.height - y) * v.scale];
export const toWorld = (v: View, sx: number, sy: number): Point => [(sx - v.ox) / v.scale, v.height - (sy - v.oy) / v.scale];

const MONO = "'JetBrains Mono Variable', ui-monospace, Consolas, monospace"; // canvas fonts cannot read CSS variables

function path(ctx: CanvasRenderingContext2D, v: View, pts: readonly (readonly number[])[], close: boolean) {
  ctx.beginPath();
  pts.forEach(([x, y], i) => {
    const [sx, sy] = toScreen(v, x, y);
    if (i) ctx.lineTo(sx, sy);
    else ctx.moveTo(sx, sy);
  });
  if (close) ctx.closePath();
}

let hatch: CanvasPattern | null = null;
function hatchPattern(ctx: CanvasRenderingContext2D) {
  if (hatch) return hatch;
  const tile = document.createElement("canvas");
  tile.width = tile.height = 8;
  const t = tile.getContext("2d")!;
  t.strokeStyle = COLORS.obstacleLine;
  t.lineWidth = 1;
  t.beginPath();
  t.moveTo(0, 8);
  t.lineTo(8, 0);
  t.stroke();
  return (hatch = ctx.createPattern(tile, "repeat"));
}

// Density heatmap: agents are splatted bilinearly into 1 m² cells (so a cell value is agents/m²),
// then the tiny image is upscaled with smoothing, which doubles as the blur.
const heat = typeof document === "undefined" ? null : document.createElement("canvas");
function drawHeatmap(ctx: CanvasRenderingContext2D, v: View, env: Environment, agents: Agent[]) {
  const cols = Math.ceil(env.width);
  const rows = Math.ceil(env.height);
  const grid = new Float32Array(cols * rows);
  for (const a of agents) {
    const gx = a.x - 0.5;
    const gy = a.y - 0.5;
    const i = Math.floor(gx);
    const j = Math.floor(gy);
    const fx = gx - i;
    const fy = gy - j;
    const add = (ci: number, cj: number, w: number) => {
      if (ci >= 0 && cj >= 0 && ci < cols && cj < rows) grid[cj * cols + ci] += w;
    };
    add(i, j, (1 - fx) * (1 - fy));
    add(i + 1, j, fx * (1 - fy));
    add(i, j + 1, (1 - fx) * fy);
    add(i + 1, j + 1, fx * fy);
  }
  heat!.width = cols;
  heat!.height = rows;
  const hctx = heat!.getContext("2d")!;
  const img = hctx.createImageData(cols, rows);
  for (let j = 0; j < rows; j++) {
    for (let i = 0; i < cols; i++) {
      const d = Math.min(grid[j * cols + i] / 3, 1); // 3 agents/m² and above saturate
      const o = ((rows - 1 - j) * cols + i) * 4; // flip y into image rows
      img.data[o] = 255;
      img.data[o + 1] = Math.round(200 - 150 * d);
      img.data[o + 2] = Math.round(70 - 50 * d);
      img.data[o + 3] = Math.round(190 * Math.sqrt(d));
    }
  }
  hctx.putImageData(img, 0, 0);
  const [x0, y0] = toScreen(v, 0, rows);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(heat!, x0, y0, cols * v.scale, rows * v.scale);
}

export function draw(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  store: RunStore,
  agents: Agent[],
  layers: Layers,
  selected: Agent["id"] | null,
  drawAgentBodies = true,
): View | null {
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, w, h);
  const env = store.env;
  if (!env) return null;
  const v = fitView(env, w, h);
  const s = v.scale;

  // the building footprint, lifted off the background
  ctx.save();
  ctx.shadowColor = "rgba(0, 0, 0, 0.55)";
  ctx.shadowBlur = 28;
  ctx.fillStyle = COLORS.floor;
  ctx.fillRect(v.ox, v.oy, env.width * s, env.height * s);
  ctx.restore();

  if (layers.grid) {
    for (let x = 0; x <= env.width; x++) {
      ctx.strokeStyle = x % 5 ? COLORS.gridMinor : COLORS.gridMajor;
      ctx.beginPath();
      ctx.moveTo(v.ox + x * s, v.oy);
      ctx.lineTo(v.ox + x * s, v.oy + env.height * s);
      ctx.stroke();
    }
    for (let y = 0; y <= env.height; y++) {
      ctx.strokeStyle = y % 5 ? COLORS.gridMinor : COLORS.gridMajor;
      const [, sy] = toScreen(v, 0, y);
      ctx.beginPath();
      ctx.moveTo(v.ox, sy);
      ctx.lineTo(v.ox + env.width * s, sy);
      ctx.stroke();
    }
    // origin marker, so everyone can check the axes match their own coordinates
    const [ox, oy] = toScreen(v, 0, 0);
    ctx.strokeStyle = ctx.fillStyle = COLORS.ink;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(ox + 26, oy + 18);
    ctx.lineTo(ox, oy + 18);
    ctx.moveTo(ox - 18, oy);
    ctx.lineTo(ox - 18, oy - 26);
    ctx.stroke();
    ctx.lineWidth = 1;
    ctx.font = `10px ${MONO}`;
    ctx.fillText("x", ox + 30, oy + 21);
    ctx.fillText("y", ox - 21, oy - 30);
    ctx.fillText("0,0", ox - 26, oy + 30);
  }

  if (layers.heatmap) drawHeatmap(ctx, v, env, agents);

  for (const o of env.obstacles) {
    path(ctx, v, o, true);
    ctx.fillStyle = COLORS.obstacleFill;
    ctx.fill();
    ctx.fillStyle = hatchPattern(ctx) ?? COLORS.obstacleFill;
    ctx.fill();
    ctx.strokeStyle = COLORS.obstacleLine;
    ctx.stroke();
  }

  ctx.lineCap = "square";
  ctx.lineJoin = "miter";
  ctx.strokeStyle = COLORS.wall;
  ctx.lineWidth = Math.max(2, 0.2 * s);
  for (const wall of env.walls) {
    path(ctx, v, wall, false);
    ctx.stroke();
  }
  ctx.lineCap = "butt";
  ctx.lineWidth = 1;

  for (const e of env.exits) {
    path(ctx, v, e.polygon, true);
    ctx.fillStyle = "rgba(47, 212, 122, 0.25)";
    ctx.fill();
    ctx.strokeStyle = COLORS.exit;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.lineWidth = 1;
  }

  if (layers.trails) {
    // each trail is stroked as a few chunks of rising opacity, not one stroke per point
    const t = store.frame?.simulation_time ?? 0;
    const CHUNKS = 6;
    ctx.lineWidth = Math.max(1, 0.06 * s);
    for (const [id, trail] of store.trails) {
      if (trail.length < 2) continue;
      const strong = id === selected;
      ctx.strokeStyle = strong ? COLORS.selected : COLORS.walking;
      ctx.lineCap = "round";
      const size = Math.ceil((trail.length - 1) / CHUNKS);
      for (let i = 0; i < trail.length - 1; i += size) {
        const chunk = trail.slice(i, i + size + 1);
        ctx.globalAlpha = (strong ? 0.95 : 0.28) * Math.max(0, 1 - (t - chunk[0][2]) / 6);
        path(ctx, v, chunk, false);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
    ctx.lineWidth = 1;
    ctx.lineCap = "butt";
  }

  if (layers.predictions) {
    ctx.strokeStyle = COLORS.prediction;
    ctx.setLineDash([4, 4]);
    for (const a of agents) {
      if (!a.predicted?.length) continue;
      ctx.globalAlpha = a.id === selected ? 1 : 0.4;
      path(ctx, v, [[a.x, a.y], ...a.predicted], false);
      ctx.stroke();
    }
    ctx.setLineDash([]);
    for (const a of agents) {
      const end = a.predicted?.at(-1);
      if (!end) continue;
      ctx.globalAlpha = a.id === selected ? 1 : 0.4;
      const [ex, ey] = toScreen(v, end[0], end[1]);
      ctx.beginPath();
      ctx.arc(ex, ey, 2.5, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  const r = Math.max(3, 0.25 * s);
  ctx.lineCap = "round";
  if (drawAgentBodies) for (const a of agents) {
    const [x, y] = toScreen(v, a.x, a.y);
    const color = stateColor(a.state);
    if (a.state === "waiting") {
      // soft halo makes jams readable at a glance
      ctx.fillStyle = "rgba(255, 90, 54, 0.16)";
      ctx.beginPath();
      ctx.arc(x, y, r * 2.4, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
    // heading notch just outside the body, pointing along the velocity
    const speed = Math.hypot(a.vx, a.vy);
    if (speed > 0.05) {
      const ux = a.vx / speed;
      const uy = -a.vy / speed;
      ctx.strokeStyle = color;
      ctx.lineWidth = Math.max(1.2, r * 0.45);
      ctx.beginPath();
      ctx.moveTo(x + ux * r * 1.35, y + uy * r * 1.35);
      ctx.lineTo(x + ux * r * 2.1, y + uy * r * 2.1);
      ctx.stroke();
    }
    if (a.id === selected) {
      ctx.strokeStyle = COLORS.selected;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, r + 6, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
  ctx.lineCap = "butt";
  ctx.lineWidth = 1;

  // exit labels go on top of agents so queues never hide them; each sits 1.4 m inside the room
  ctx.font = `600 10px ${MONO}`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (const e of env.exits) {
    const cx = e.polygon.reduce((t, p) => t + p[0], 0) / e.polygon.length;
    const cy = e.polygon.reduce((t, p) => t + p[1], 0) / e.polygon.length;
    const dx = env.width / 2 - cx;
    const dy = env.height / 2 - cy;
    const along = Math.abs(dx) / env.width > Math.abs(dy) / env.height;
    const [lx, ly] = toScreen(v, cx + (along ? Math.sign(dx) * 1.4 : 0), cy + (along ? 0 : Math.sign(dy) * 1.4));
    const label = `EXIT ${e.id}`;
    const tw = ctx.measureText(label).width + 10;
    ctx.fillStyle = COLORS.exit;
    ctx.beginPath();
    ctx.roundRect(lx - tw / 2, ly - 8, tw, 16, 3);
    ctx.fill();
    ctx.fillStyle = "#052514";
    ctx.fillText(label, lx, ly + 0.5);
  }
  ctx.textAlign = "start";
  ctx.textBaseline = "alphabetic";

  // scale bar, bottom right
  const bar = 5 * s;
  const bx = w - 24 - bar;
  const by = h - 18;
  ctx.strokeStyle = ctx.fillStyle = COLORS.ink;
  ctx.beginPath();
  ctx.moveTo(bx, by - 4);
  ctx.lineTo(bx, by);
  ctx.lineTo(bx + bar, by);
  ctx.lineTo(bx + bar, by - 4);
  ctx.stroke();
  ctx.font = `10px ${MONO}`;
  ctx.textAlign = "center";
  ctx.fillText("5 m", bx + bar / 2, by - 6);
  ctx.textAlign = "start";
  return v;
}
