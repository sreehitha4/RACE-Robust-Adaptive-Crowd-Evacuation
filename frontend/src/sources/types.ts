import type { Environment, Frame } from "../contract.ts";

export type Tone = "ok" | "warn" | "error";

/** Where a data source pushes what it produces. The app implements this once for every source. */
export interface Sink {
  environment(env: Environment): void;
  frame(frame: Frame): void;
  status(text: string, tone: Tone): void; // header badge
  error(text: string): void; // dismissable banner
  stopped(): void; // the source stopped on its own (finished, ended, disconnected)
}

/** Mock, live backend and replay file all expose the same transport controls. */
export interface Source {
  start(): Promise<void>;
  pause(): Promise<void>;
  reset(): Promise<void>;
  close(): void;
}
