# RACE data contract (frontend ⇄ simulation / backend)

This is what the browser viewer accepts. It is enforced by `src/contract.ts`. A message that breaks the
contract is rejected, and the viewer shows a banner that names the offending field, for example
`message.agents[3].y should be a finite number, got null`. One bad message does not stop the stream.

## Conventions

| | |
|---|---|
| Units | metres, seconds, m/s |
| Axes | origin at the **bottom-left** of the floor, x to the right, **y up** (same as Shapely and ETH-UCY world coordinates) |
| Points | `[x, y]` arrays of two numbers |
| Rate | about 10 frames per second while running; the viewer interpolates between frames |
| Numbers | must be finite (`NaN`/`Infinity` are rejected, so convert NumPy values with `float(...)`) |

## Transport (workstream 4, FastAPI on port 8000)

| What | Endpoint |
|---|---|
| Updates | WebSocket `ws://<host>:8000/ws/simulation` |
| Start / resume | `POST /api/simulation/start` |
| Pause | `POST /api/simulation/pause` |
| Reset | `POST /api/simulation/reset` |

- On every new WebSocket connection, send one `environment` message, then the current `frame`.
- After a reset, send the `environment` again, then the frame at `simulation_time: 0`.
- REST calls only need to return a 2xx status. Any other status is shown to the user as an error.
- The dev server proxies `/api` and `/ws` to the backend, so CORS is not needed in development.

## `environment` message

```json
{
  "type": "environment",
  "width": 40,
  "height": 24,
  "walls": [[[0, 0], [40, 0], [40, 14]], [[14, 0], [14, 4]]],
  "obstacles": [[[3.5, 3.5], [7, 3.5], [7, 5.5], [3.5, 5.5]]],
  "exits": [{ "id": "W", "polygon": [[0, 10], [0.6, 10], [0.6, 12.5], [0, 12.5]] }]
}
```

| Field | Type | Notes |
|---|---|---|
| `width`, `height` | number | floor size in metres |
| `walls` | list of polylines | each needs ≥ 2 points; Shapely: `list(line.coords)` |
| `obstacles` | list of polygons | each needs ≥ 3 points; Shapely: `list(poly.exterior.coords)` |
| `exits` | list of `{id, polygon}` | `id` is a string or number; polygon needs ≥ 3 points |

## `frame` message

```json
{
  "type": "frame",
  "simulation_time": 12.4,
  "total_agents": 200,
  "evacuated": 57,
  "density": 0.18,
  "prediction_model": "lstm",
  "agents": [
    { "id": 1, "x": 10.5, "y": 6.2, "vx": 0.8, "vy": -0.3, "state": "walking",
      "predicted": [[10.8, 6.1], [11.1, 6.0]] }
  ]
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `simulation_time` | number | yes | seconds since the run started; if it goes backwards the viewer treats it as a new run |
| `total_agents` | number | yes | agents at the start of the run |
| `evacuated` | number | yes | agents that have left so far |
| `agents` | list | yes | agents still in the building (see below) |
| `density` | number | no | agents per m² of walkable floor; shown as "Density", or "—" if missing |
| `prediction_model` | string | no | label shown next to predicted paths, e.g. `"lstm"` |

### Agent

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string or number | yes | must stay the same for one agent across frames (used for interpolation and trails) |
| `x`, `y` | number | yes | position in metres |
| `vx`, `vy` | number | yes | velocity in m/s (used for the heading marker and mean speed) |
| `state` | string | yes | `"walking"`, `"waiting"` (counted as congested, drawn red-orange) or `"evacuated"`; any other value is drawn grey |
| `predicted` | list of points | no | future positions from the trajectory model (workstream 1), nearest first. ETH-UCY style is 12 points at 0.4 s steps |

Evacuated agents can be left out of `agents` or sent with `state: "evacuated"`. Either works, and they are
not drawn.

## Replay files

The **Replay file** button loads a recorded run. It is the easiest way to show workstream 2's output before
the backend is wired up:

```json
{
  "environment": { "width": 40, "height": 24, "walls": [], "obstacles": [], "exits": [] },
  "frames": [{ "simulation_time": 0, "total_agents": 200, "evacuated": 0, "agents": [] }]
}
```

The `type` fields are optional in files. Everything else is validated in the same way as live messages,
and errors point at the field, e.g. `frames[12].agents[0].x`. Frames play back at their `simulation_time`.

Python sketch for the simulation side:

```python
import json
run = {"environment": env_dict, "frames": []}
for step in range(n_steps):
    sim.step(dt)
    run["frames"].append(sim.to_frame_dict())   # same shape as the frame message
json.dump(run, open("run.json", "w"))
```

## To confirm with the team

1. **Backend (hardhick):** are the endpoint names `/ws/simulation` and `/api/simulation/{start,pause,reset}`?
   If they differ, change `WS_PATH` / `API_PATH` in `src/sources/live.ts`. Is it "pause" or "stop"?
2. **Simulation (keerthana):** is the origin bottom-left with y up? Are walls LineStrings and obstacles
   Polygons? Is `"waiting"` the state for agents held up in a queue?
3. **Prediction (Sreehitha):** is the horizon 12 points at 0.4 s, and are points in world metres (not pixels
   or normalised)?
