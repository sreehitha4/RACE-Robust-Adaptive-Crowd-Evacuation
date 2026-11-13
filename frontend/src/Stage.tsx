import { useEffect, useRef } from "react";
import type { Agent } from "./contract.ts";
import { draw, toWorld, type Layers, type View } from "./render.ts";
import type { RunStore } from "./store.ts";
import { WebGLAgentRenderer } from "./webglAgents.ts";

interface Props {
  store: RunStore;
  layers: Layers;
  selected: Agent["id"] | null;
  onSelect(id: Agent["id"] | null): void;
}

/** The floor-plan canvas. Draws every animation frame from the store; React only passes options in. */
export function Stage({ store, layers, selected, onSelect }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const webglRef = useRef<HTMLCanvasElement>(null);
  const readoutRef = useRef<HTMLDivElement>(null);
  const performanceRef = useRef<HTMLDivElement>(null);
  const live = useRef({ layers, selected, view: null as View | null, agents: [] as Agent[] });
  live.current.layers = layers;
  live.current.selected = selected;

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    let webgl: WebGLAgentRenderer | null = null;
    try { if (webglRef.current) webgl = new WebGLAgentRenderer(webglRef.current); } catch { webgl = null; }
    let raf = 0;
    let frames = 0;
    let windowStarted = performance.now();
    const loop = () => {
      const renderStarted = performance.now();
      const dpr = window.devicePixelRatio || 1;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
        canvas.width = Math.round(w * dpr);
        canvas.height = Math.round(h * dpr);
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const l = live.current;
      l.agents = store.agentsAt(performance.now());
      l.view = draw(ctx, w, h, store, l.agents, l.layers, l.selected, !webgl);
      if (webgl && l.view) webgl.draw(l.agents, l.view, w, h, dpr, l.selected);
      frames += 1;
      const now = performance.now();
      if (now - windowStarted >= 500) {
        const fps = Math.round(frames * 1000 / (now - windowStarted));
        const renderMs = now - renderStarted;
        if (performanceRef.current) performanceRef.current.textContent = `${fps} FPS · ${renderMs.toFixed(1)} ms · ${l.agents.length} agents`;
        frames = 0;
        windowStarted = now;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => { cancelAnimationFrame(raf); webgl?.dispose(); };
  }, [store]);

  const worldAt = (e: React.PointerEvent | React.MouseEvent) => {
    const v = live.current.view;
    if (!v) return null;
    const r = canvasRef.current!.getBoundingClientRect();
    return toWorld(v, e.clientX - r.left, e.clientY - r.top);
  };

  return (
    <div className="stage">
      <canvas
        ref={canvasRef}
        role="img"
        aria-label="Floor plan with walls, obstacles, exits and moving pedestrian agents"
        onPointerMove={(e) => {
          const p = worldAt(e);
          const env = store.env;
          const inside = p && env && p[0] >= 0 && p[1] >= 0 && p[0] <= env.width && p[1] <= env.height;
          readoutRef.current!.textContent = inside ? `x ${p[0].toFixed(2)} m   y ${p[1].toFixed(2)} m` : "";
        }}
        onPointerLeave={() => (readoutRef.current!.textContent = "")}
        onClick={(e) => {
          const p = worldAt(e);
          if (!p) return;
          let best: Agent | null = null;
          let bestD = 0.8; // metres: generous so moving agents are easy to catch
          for (const a of live.current.agents) {
            const d = Math.hypot(a.x - p[0], a.y - p[1]);
            if (d < bestD) [best, bestD] = [a, d];
          }
          onSelect(best?.id ?? null);
        }}
      />
      <canvas ref={webglRef} className="stage-webgl" aria-hidden="true" />
      <div className="readout" ref={readoutRef} aria-hidden />
      <div className="performance-readout" ref={performanceRef} aria-hidden="true">Measuring renderer…</div>
    </div>
  );
}
