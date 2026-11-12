// Live backend (workstream 4): controls go over REST, updates arrive on one WebSocket.
// In development Vite proxies /api and /ws to the FastAPI server (see vite.config.ts).
import { parseMessage } from "../contract.ts";
import type { Sink, Source } from "./types.ts";

export const WS_PATH = "/ws/simulation";
export const API_PATH = "/api/simulation";

export function createLiveSource(sink: Sink): Source {
  const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}${WS_PATH}`;
  let ws: WebSocket | undefined;
  let retry: ReturnType<typeof setTimeout> | undefined;
  let closed = false;

  const connect = () => {
    sink.status(`Connecting to ${WS_PATH}…`, "warn");
    ws = new WebSocket(url);
    ws.onopen = () => sink.status(`Live · ${WS_PATH}`, "ok");
    ws.onmessage = (e) => {
      try {
        const msg = parseMessage(JSON.parse(e.data));
        if (msg.type === "environment") sink.environment(msg);
        else sink.frame(msg);
      } catch (err) {
        // one bad message should not kill the stream; show it so the backend can be fixed
        sink.error(`Rejected backend message: ${(err as Error).message}`);
      }
    };
    ws.onclose = () => {
      if (closed) return;
      sink.stopped();
      sink.status("Backend offline · retrying every 2 s", "error");
      retry = setTimeout(connect, 2000);
    };
  };

  const post = async (action: string) => {
    const res = await fetch(`${API_PATH}/${action}`, { method: "POST" });
    if (!res.ok) throw new Error(`POST ${API_PATH}/${action} failed with HTTP ${res.status}`);
  };

  connect();
  return {
    start: () => post("start"),
    pause: () => post("pause"),
    reset: () => post("reset"),
    close() {
      closed = true;
      clearTimeout(retry);
      ws?.close();
    },
  };
}
