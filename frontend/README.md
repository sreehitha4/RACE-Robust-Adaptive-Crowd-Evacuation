# RACE · Crowd Evacuation Viewer (Workstream 3)

This is the browser frontend for **RACE (Robust Crowd Evacuation)**. It draws the floor plan and the moving
crowd on an HTML Canvas, gives start/pause/reset controls and shows live evacuation metrics. It is built with
React and TypeScript. It does not use Pygame.

It can run on three data sources, all through one interface:

| Source | What it is | When to use it |
|---|---|---|
| **Mock data** | A small synthetic crowd simulated in the browser. It is always labelled *"Mock data · synthetic"* | UI work and demos before the backend exists |
| **Live backend** | WebSocket `/ws/simulation` and REST `/api/simulation/*` from the FastAPI server (workstream 4) | The real system |
| **Replay file** | A JSON recording of a run (workstream 2 output) | Showing real simulation output without the backend |

Mock numbers are not RACE results. The mock is only there so the viewer can be built and tested. The badge
in the top-right always says which source is on screen.

## Requirements

- Node.js **20.19+ or 22.12+** (`node -v`)
- For live mode: the FastAPI backend running (default `http://localhost:8000`)

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

To point at a backend that is not on `localhost:8000`, set `RACE_BACKEND`.

macOS/Linux:

```bash
RACE_BACKEND=http://192.168.1.20:8000 npm run dev
```

Windows PowerShell:

```powershell
$env:RACE_BACKEND="http://192.168.1.20:8000"; npm run dev
```

Other commands:

```bash
npm test
```

```bash
npm run build
```

`npm test` runs the unit tests (contract validation, mock sim, replay parsing, store). `npm run build` type-checks and builds to `dist/`.

## What is on screen

- **Floor plan:** walls, hatched obstacles and green exits, drawn to scale. The y axis points up and the origin is bottom-left. A 5 m scale bar and a cursor readout in metres are included.
- **Agents:** a dot with a heading notch, interpolated smoothly between frames. Agents that are walking are ivory. Agents that are congested (`state: "waiting"`) are red-orange with a halo.
- **Layers** (toggle chips):
  - **Trails:** the last 6 s of each path.
  - **Forecast:** the predicted paths from the trajectory model (workstream 1), labelled with `prediction_model`.
  - **Density:** a heatmap computed from positions in 1 m cells, saturating at 3 agents/m².
  - **Grid:** a 1 m / 5 m grid.
- **Agent inspector:** click an agent to follow it and see its id, state, position, speed and forecast.
- **Stats:**
  - Agents, evacuated, remaining and simulation time.
  - A gauge showing the share evacuated, and an evacuation curve.
  - Crowd metrics: density, exit flow, mean speed, congested count, T50 and T90.

### Metric definitions

| Metric | Meaning |
|---|---|
| Density | `density` from the frame: agents per m² of walkable floor (shown as "—" if not sent) |
| Exit flow | agents evacuated per second, averaged over the last 5 s of simulation time |
| Mean speed | mean of `√(vx² + vy²)` over agents still inside |
| Congested | agents whose `state` is `"waiting"` |
| T50 / T90 | simulation time when 50% / 90% of `total_agents` had evacuated |

### Controls

| Key | Action |
|---|---|
| `Space` | start / pause |
| `R` | reset |
| `Esc` | deselect agent |

## Data interface

The full wire format is in **[CONTRACT.md](CONTRACT.md)**, which can be shared with the backend and simulation
teammates. In short:

- The viewer receives one `environment` message (walls, obstacles, exits).
- It then receives a stream of `frame` messages (`simulation_time`, `agents[]`, `total_agents`, `evacuated`, optional `density` and `predicted` paths).
- Every incoming message is validated. A bad one shows a banner that names the field and does not crash the stream.

## Project structure

```
src/
  contract.ts       wire types + validation (the data interface)
  sources/
    types.ts        Source / Sink interface every data source implements
    mock.ts         synthetic in-browser crowd (flow field + social force)
    live.ts         WebSocket + REST client for the FastAPI backend
    replay.ts       JSON recording player
  store.ts          frame buffer: interpolation, trails, evacuation series, T50/T90, flow
  render.ts         all Canvas drawing (pure function of store + layer options)
  Stage.tsx         canvas element, animation loop, hover readout, click-to-select
  App.tsx           layout, controls, stats panels
  styles.css        design tokens and layout
tests/
  frontend.test.ts  node:test unit tests
```

To add a new data source, implement `Source` from `src/sources/types.ts` and push messages into the `Sink`.
Nothing else needs to change.

## Mock simulation (what it is and isn't)

The mock lays out a 40 × 24 m floor with three exits. It places 200 agents and moves them with these rules:

- Each agent walks down a Dijkstra distance-to-exit field.
- Agents push each other apart with an exponential social force.
- Agents slide along walls.

Its forecast is plain constant velocity, labelled `constant-velocity (mock)`. It is good enough to show
queues forming at doorways. It is **not** the RACE simulation engine or the LSTM, so do not report its numbers
as results.
