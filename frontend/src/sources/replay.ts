// Plays back a recorded run: { "environment": {...}, "frames": [{...}, ...] }.
// This is how the simulation engine's JSON output can be viewed before the backend is ready.
import { parseMessage, type Environment, type Frame } from "../contract.ts";
import type { Sink, Source } from "./types.ts";

export interface Recording {
  environment: Environment;
  frames: Frame[];
}

/** The `type` fields are optional in files; everything else is validated like a live message. */
export function parseReplay(text: string): Recording {
  const raw = JSON.parse(text);
  if (!Array.isArray(raw?.frames) || raw.frames.length === 0) throw new Error("replay file needs a non-empty \"frames\" array");
  return {
    environment: parseMessage({ type: "environment", ...raw.environment }, "environment") as Environment,
    frames: raw.frames.map((f: object, i: number) => parseMessage({ type: "frame", ...f }, `frames[${i}]`) as Frame),
  };
}

export function createReplaySource(sink: Sink, name: string, run: Recording): Source {
  const { frames } = run;
  let i = 0;
  let base = 0; // performance.now() that lines up with frames[0].simulation_time
  let timer: ReturnType<typeof setInterval> | undefined;
  const stop = () => {
    clearInterval(timer);
    timer = undefined;
  };
  const rewind = () => {
    i = 0;
    sink.environment(run.environment);
    sink.frame(frames[0]);
  };
  sink.status(`Replay · ${name} · ${frames.length} frames`, "ok");
  rewind();
  return {
    async start() {
      if (timer) return;
      if (i === frames.length - 1) rewind();
      base = performance.now() - (frames[i].simulation_time - frames[0].simulation_time) * 1000;
      timer = setInterval(() => {
        const t = frames[0].simulation_time + (performance.now() - base) / 1000;
        let j = i;
        while (j + 1 < frames.length && frames[j + 1].simulation_time <= t) j++;
        if (j !== i) sink.frame(frames[(i = j)]);
        if (i === frames.length - 1) {
          stop();
          sink.stopped();
        }
      }, 16);
    },
    async pause() {
      stop();
    },
    async reset() {
      stop();
      rewind();
    },
    close: stop,
  };
}
