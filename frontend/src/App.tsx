import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import type { Agent } from "./contract.ts";
import { COLORS, stateColor, type Layers } from "./render.ts";
import { createLiveSource, WS_PATH } from "./sources/live.ts";
import { createMockSource } from "./sources/mock.ts";
import { createReplaySource, parseReplay, type Recording } from "./sources/replay.ts";
import type { Sink, Source, Tone } from "./sources/types.ts";
import { Stage } from "./Stage.tsx";
import { RunStore } from "./store.ts";

type Choice = { kind: "mock" } | { kind: "live" } | { kind: "replay"; name: string; run: Recording };

const LAYER_CHIPS: [keyof Layers, string, string][] = [
  ["trails", "Trails", "Last 6 s of every agent's path"],
  ["predictions", "Forecast", "Future positions from the trajectory model"],
  ["heatmap", "Density", "Local crowd density, agents per m²"],
  ["grid", "Grid", "1 m grid with the origin marked"],
];

const clock = (t: number) => {
  const m = Math.floor(t / 60);
  return `${String(m).padStart(2, "0")}:${(t - m * 60).toFixed(1).padStart(4, "0")}`;
};
const fixed = (n: number | undefined, digits: number) => (n === undefined ? "—" : n.toFixed(digits));

export function App() {
  const store = useMemo(() => new RunStore(), []);
  const [, bump] = useReducer((n: number) => n + 1, 0);
  const [choice, setChoice] = useState<Choice>({ kind: "mock" });
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<{ text: string; tone: Tone }>({ text: "", tone: "warn" });
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Agent["id"] | null>(null);
  const [layers, setLayers] = useState<Layers>({ grid: true, trails: true, predictions: false, heatmap: false });
  const source = useRef<Source | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const sink = useMemo<Sink>(
    () => ({
      environment: (env) => {
        store.setEnvironment(env);
        bump();
      },
      frame: (f) => {
        store.push(f, performance.now());
        bump();
      },
      status: (text, tone) => setStatus({ text, tone }),
      error: setError,
      stopped: () => setRunning(false),
    }),
    [store],
  );

  useEffect(() => {
    store.env = null;
    store.clear();
    setRunning(false);
    setSelected(null);
    setError(null);
    const src =
      choice.kind === "mock"
        ? createMockSource(sink)
        : choice.kind === "live"
          ? createLiveSource(sink)
          : createReplaySource(sink, choice.name, choice.run);
    source.current = src;
    bump();
    return () => src.close();
  }, [choice, sink, store]);

  const act = async (action: "start" | "pause" | "reset") => {
    try {
      await source.current?.[action]();
      setRunning(action === "start");
      if (action === "reset") setSelected(null);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).closest("button, input, select, textarea")) return;
      if (e.code === "Space") {
        e.preventDefault();
        act(running ? "pause" : "start");
      } else if (e.key === "r" || e.key === "R") act("reset");
      else if (e.key === "Escape") setSelected(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const openReplay = async (file: File) => {
    try {
      setChoice({ kind: "replay", name: file.name, run: parseReplay(await file.text()) });
    } catch (e) {
      setError(`Could not load ${file.name}: ${(e as Error).message}`);
    }
  };

  const env = store.env;
  const f = store.frame;
  const t = f?.simulation_time ?? 0;
  const active = f?.agents.filter((a) => a.state !== "evacuated") ?? [];
  const total = f?.total_agents ?? 0;
  const evacuated = f?.evacuated ?? 0;
  const share = total ? evacuated / total : 0;
  const waiting = active.filter((a) => a.state === "waiting").length;
  const meanSpeed = active.length ? active.reduce((s, a) => s + Math.hypot(a.vx, a.vy), 0) / active.length : undefined;
  const picked = active.find((a) => a.id === selected);
  const t50 = store.timeTo(0.5);
  const t90 = store.timeTo(0.9);
  const done = total > 0 && evacuated >= total;
  const phase = done ? "cleared" : running ? "running" : t > 0 ? "paused" : "ready";

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <svg viewBox="0 0 40 40" className="mark" aria-hidden>
            <rect x="2" y="2" width="36" height="36" rx="9" />
            <path d="M12 28V12h9a5 5 0 0 1 0 10h-9M20 22l7 6" />
          </svg>
          <div>
            <h1>RACE</h1>
            <p>Robust Crowd Evacuation</p>
          </div>
        </div>
        <nav className="segmented" aria-label="Data source">
          {(["mock", "live"] as const).map((k) => (
            <button key={k} aria-pressed={choice.kind === k} onClick={() => choice.kind !== k && setChoice({ kind: k })}>
              {k === "mock" ? "Mock data" : "Live backend"}
            </button>
          ))}
          <button aria-pressed={choice.kind === "replay"} onClick={() => fileInput.current!.click()}>
            Replay file
          </button>
          <input
            ref={fileInput}
            type="file"
            accept=".json,application/json"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              if (file) openReplay(file);
            }}
          />
        </nav>
        <div className={`pill ${status.tone}`} role="status">
          <span className="dot" />
          <span className="pill-text">{status.text}</span>
        </div>
      </header>

      <main className="floor card">
        <div className="floor-bar">
          <div>
            <h2>Floor plan</h2>
            <p>{env ? `${env.width} × ${env.height} m · ${env.exits.length} exits · ${env.obstacles.length} obstacles` : "No environment yet"}</p>
          </div>
          <div className="chips" role="group" aria-label="Layers">
            {LAYER_CHIPS.map(([key, label, hint]) => (
              <button key={key} className="chip" title={hint} aria-pressed={layers[key]} onClick={() => setLayers({ ...layers, [key]: !layers[key] })}>
                <i aria-hidden />
                {label}
              </button>
            ))}
          </div>
        </div>
        <div className="floor-body">
          <Stage store={store} layers={layers} selected={selected} onSelect={setSelected} />
          {error && (
            <div className="banner" role="alert">
              <span>{error}</span>
              <button onClick={() => setError(null)} aria-label="Dismiss error">
                ×
              </button>
            </div>
          )}
          {!env && <div className="empty">Waiting for the backend to send an environment on {WS_PATH}…</div>}
          <div className="legend">
            <span><i className="swatch" style={{ background: COLORS.walking }} />Walking</span>
            <span><i className="swatch halo" style={{ background: COLORS.waiting }} />Congested</span>
            <span><i className="swatch exit" />Exit</span>
            {layers.predictions && <span><i className="dash" />Forecast · {f?.prediction_model ?? "no model data"}</span>}
            {layers.heatmap && <span className="ramp">0<i />3+ /m²</span>}
          </div>
        </div>
      </main>

      <aside className="side">
        <section className="card hero">
          <div className="hero-top">
            <Gauge share={share} done={done} />
            <div className="time">
              <span className="eyebrow">Simulation time</span>
              <div className="clock">{clock(t)}</div>
              <span className={`phase ${phase}`}>{phase}</span>
            </div>
          </div>
          <dl className="counts">
            <div><dt>Agents</dt><dd>{total}</dd></div>
            <div><dt>Remaining</dt><dd>{total - evacuated}</dd></div>
            <div className="good"><dt>Evacuated</dt><dd>{evacuated}</dd></div>
          </dl>
          <div className="transport">
            <button className={`primary ${running ? "running" : ""}`} onClick={() => act(running ? "pause" : "start")} disabled={!env}>
              {running ? "Pause" : done ? "Run again" : t > 0 ? "Resume" : "Start"}
            </button>
            <button className="ghost" onClick={() => act("reset")} disabled={!env}>
              Reset
            </button>
          </div>
          <p className="keys"><kbd>Space</kbd> start / pause <kbd>R</kbd> reset <kbd>Esc</kbd> deselect</p>
        </section>

        <section className="card">
          <h3>Crowd metrics</h3>
          <dl className="kpis">
            <div title="Agents per m² of walkable floor"><dt>Density</dt><dd>{fixed(f?.density, 3)}<small>/m²</small></dd></div>
            <div title="Agents leaving per second, averaged over the last 5 s"><dt>Exit flow</dt><dd>{store.flow().toFixed(2)}<small>/s</small></dd></div>
            <div><dt>Mean speed</dt><dd>{fixed(meanSpeed, 2)}<small>m/s</small></dd></div>
            <div className={waiting ? "hot" : ""}><dt>Congested</dt><dd>{waiting}<small>agents</small></dd></div>
            <div title="Time until half of all agents had evacuated"><dt>T50</dt><dd>{fixed(t50, 1)}<small>s</small></dd></div>
            <div title="Time until 90% of all agents had evacuated"><dt>T90</dt><dd>{fixed(t90, 1)}<small>s</small></dd></div>
          </dl>
        </section>

        <section className="card">
          <h3>Evacuation curve<span>share evacuated over time</span></h3>
          <Curve series={store.series} total={total} t50={t50} t90={t90} />
        </section>

        <section className="card">
          <h3>Agent inspector</h3>
          {picked ? (
            <dl className="inspect">
              <div><dt>Agent</dt><dd>#{picked.id}</dd></div>
              <div><dt>State</dt><dd style={{ color: stateColor(picked.state) }}>{picked.state}</dd></div>
              <div><dt>Position</dt><dd>{picked.x.toFixed(2)}, {picked.y.toFixed(2)} m</dd></div>
              <div><dt>Velocity</dt><dd>{picked.vx.toFixed(2)}, {picked.vy.toFixed(2)} m/s</dd></div>
              <div><dt>Speed</dt><dd>{Math.hypot(picked.vx, picked.vy).toFixed(2)} m/s</dd></div>
              <div><dt>Forecast</dt><dd>{picked.predicted?.length ? `${picked.predicted.length} points` : "none"}</dd></div>
            </dl>
          ) : (
            <p className="hint">{selected !== null ? `Agent #${selected} has left the building.` : "Click any agent on the floor plan to follow it."}</p>
          )}
        </section>
      </aside>
    </div>
  );
}

function Gauge({ share, done }: { share: number; done: boolean }) {
  const r = 40;
  const c = 2 * Math.PI * r;
  return (
    <svg viewBox="0 0 100 100" className={`gauge ${done ? "done" : ""}`} role="img" aria-label={`${Math.round(share * 100)}% evacuated`}>
      {Array.from({ length: 48 }, (_, i) => (
        <line key={i} x1="50" y1="2" x2="50" y2={i % 6 ? "5" : "7"} transform={`rotate(${i * 7.5} 50 50)`} className={i / 48 < share ? "tick on" : "tick"} />
      ))}
      <circle cx="50" cy="50" r={r} className="track" />
      <circle cx="50" cy="50" r={r} className="fill" strokeDasharray={c} strokeDashoffset={c * (1 - share)} transform="rotate(-90 50 50)" />
      <text x="50" y="52" className="pct">{Math.round(share * 100)}%</text>
      <text x="50" y="66" className="sub">{done ? "CLEARED" : "EVACUATED"}</text>
    </svg>
  );
}

function Curve({ series, total, t50, t90 }: { series: [number, number][]; total: number; t50?: number; t90?: number }) {
  const W = 300;
  const H = 120;
  const t0 = series[0]?.[0] ?? 0;
  const span = Math.max(20, (series.at(-1)?.[0] ?? 0) - t0);
  const x = (t: number) => ((t - t0) / span) * W;
  const y = (e: number) => H - (e / Math.max(total, 1)) * H;
  const pts = series.map(([t, e]) => `${x(t).toFixed(1)},${y(e).toFixed(1)}`).join(" ");
  const last = series.at(-1);
  return (
    <figure className="curve">
      <div className="plot">
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label="Evacuated agents over time">
          <defs>
            <linearGradient id="curve-fill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" stopColor={COLORS.exit} stopOpacity="0.32" />
              <stop offset="1" stopColor={COLORS.exit} stopOpacity="0" />
            </linearGradient>
          </defs>
          {[0.5, 0.9].map((p) => (
            <line key={p} x1="0" x2={W} y1={H - p * H} y2={H - p * H} className="guide" />
          ))}
          {[t50, t90].map((t, i) => t !== undefined && <line key={i} x1={x(t)} x2={x(t)} y1="0" y2={H} className="guide marker" />)}
          {last && <polygon points={`0,${H} ${pts} ${x(last[0])},${H}`} fill="url(#curve-fill)" />}
          {last && <polyline points={pts} fill="none" stroke={COLORS.exit} strokeWidth="2.5" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />}
        </svg>
        <span className="tag" style={{ top: "10%" }}>90%</span>
        <span className="tag" style={{ top: "50%" }}>50%</span>
      </div>
      <figcaption>
        <span>{t0.toFixed(0)} s</span>
        <span>{(t0 + span).toFixed(0)} s</span>
      </figcaption>
    </figure>
  );
}
