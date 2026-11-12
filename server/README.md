# RACE Backend (Workstream 4)

FastAPI integration layer for the existing React + TypeScript frontend.

## Current status

The API, WebSocket transport, schemas, lifecycle manager and test suite are implemented against `frontend/CONTRACT.md`.

**Important:** `MockSimulationAdapter` is only a deterministic integration placeholder. It is not Keerthana's final simulation engine and must be replaced by an adapter around that engine when its code is available.

## Run locally (PowerShell)

From the repository root:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r server/requirements.txt
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal. The frontend proxies `/api` and `/ws` to `http://localhost:8000`.

## API

- `GET /health`
- `POST /api/simulation/start`
- `POST /api/simulation/pause`
- `POST /api/simulation/reset`
- `GET /api/simulation/status`
- `WS /ws/simulation`

Each WebSocket connection receives `environment` then `frame`. Running simulations broadcast frames at approximately 10 Hz. Reset broadcasts environment followed by a time-zero frame.

## Tests

From the repository root:

```powershell
pytest server/tests -q
```

## ML adapter

`TrajectoryPredictionAdapter` lazily attempts to load the LSTM checkpoint. Set `RACE_ML_CHECKPOINT` to its path. If the checkpoint or PyTorch is unavailable, prediction uses constant velocity. The adapter returns 12 predicted points by default.

The prediction adapter is separate from simulation movement. Predictions are advisory; the simulation engine remains responsible for actual movement, obstacle avoidance and evacuation behaviour.

## Replacing the mock simulation

Implement the `SimulationAdapter` protocol in `server/adapters/base.py`:

- `environment() -> EnvironmentMessage`
- `frame() -> FrameMessage`
- `step(dt: float) -> None`
- `reset() -> None`

Then replace `MockSimulationAdapter()` in `server/main.py` with an adapter for Keerthana's engine. Keep frontend-facing schemas and endpoints unchanged unless the team explicitly agrees to a contract revision.
