# RACE production-oriented architecture upgrade

This release adds an integrated first production-hardening layer while preserving the existing React live contract (`/ws/simulation`, `/api/simulation/start|pause|reset`). Run from the repository root unless noted.

## What is implemented

| Area | Included now | Important boundary |
|---|---|---|
| Real backend orchestration | FastAPI owns the real `CrowdSimulation`, lifecycle, REST controls and WebSocket frames | One live simulation instance per API process |
| Observability | Prometheus counters/gauges/histograms, structured logs, optional OpenTelemetry FastAPI + manual simulation/inference spans | Set `RACE_OTEL_ENABLED=true`; collector is included in Compose |
| ML serving | Measured PyTorch inference, strict `(8,2)->(12,2)` validation, model inventory and candidate-load-before-activate | ONNX is an optional export/runtime path, not the default |
| Model lifecycle | Versioned `.pth` files in `simulation_environment/ml/models`, atomic active pointer and activation endpoint | Uploading/training new model weights is not exposed as an HTTP feature yet |
| Spatial acceleration | Per-tick quadtree index for local collision/separation candidates, with movement margin for sequential agent updates | Physics still requires profiling at target population sizes |
| Event-driven work | Redis Pub/Sub telemetry channel and optional Celery worker for offline dataset validation | Live WebSocket fan-out is still process-local; Redis is not yet a shared session coordinator |
| Distributed compute | Optional Ray batch-scenario endpoint and Ray Compose overlay | Ray jobs are offline scenario sweeps, not per-frame distributed physics |
| Frontend performance | WebGL2 point-sprite layer for agent bodies with Canvas fallback; Canvas continues to render floor-plan geometry, trails and prediction paths; FPS/render-time/agent-count overlay | WebGPU and full-scene GPU rendering remain future optimizations |
| Collaboration | Optional Yjs/y-websocket sidecar | The current UI does not yet expose collaborative editing; auth and persistence are required before production |
| Deployment | Backend/frontend Dockerfiles, Compose stack, Prometheus, Grafana, Jaeger/OTel Collector, Kubernetes manifests | API deployment intentionally starts at one replica until shared simulation ownership is implemented |

## Local setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r server\requirements.txt
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL shown in the terminal. The Vite proxy forwards `/api` and `/ws` to port 8000.

## API surface

- `GET /health` and `GET /ready`
- `GET /metrics` (Prometheus)
- `GET /api/simulation/status`
- `POST /api/simulation/start`, `/pause`, `/reset`
- `GET /api/v1/ml/status`
- `POST /api/v1/ml/predict` with `{ "observed_positions": [[x,y], ... 8 points] }`
- `GET /api/v1/ml/models`
- `POST /api/v1/ml/models/{model_id}/activate`
- `POST /api/v1/datasets/upload` multipart field `file`; CSV columns: `pedestrian_id,frame,x,y`
- `GET /api/v1/datasets`
- `POST /api/v1/datasets/{dataset_id}/validate-async` (Celery optional)
- `GET /api/v1/jobs/{job_id}` (Celery optional)
- `POST /api/v1/simulation/batch` and `GET /api/v1/simulation/batch/{job_id}` (Ray optional)
- `WS /ws/simulation`: sends `environment`, then `frame`; reset rebroadcasts both

## Docker Compose

Start API, frontend, Redis, Prometheus, Grafana, Jaeger and OpenTelemetry Collector:

```bash
docker compose up --build
```

- Dashboard: `http://localhost:3000` (default user `admin`; set `GRAFANA_PASSWORD` before deployment)
- Prometheus: `http://localhost:9090`
- Jaeger: `http://localhost:16686`
- API: `http://localhost:8000`
- Frontend: `http://localhost:8080`

Start the offline Celery worker:

```bash
docker compose --profile workers up --build
```

Start the optional Yjs sidecar:

```bash
docker compose --profile collaboration up --build
```

Start the optional Ray cluster and API image with Ray installed:

```bash
docker compose -f docker-compose.yml -f docker-compose.distributed.yml up --build
```

For ONNX inference, first install `ml/requirements-onnx.txt` in a model-export environment and export:

```bash
python -m ml.export_onnx --checkpoint simulation_environment/ml/models/trajectory_lstm_best.pth --output simulation_environment/ml/models/race_lstm.onnx
```

Then set `RACE_ML_BACKEND=onnx` and `RACE_ONNX_MODEL_PATH=simulation_environment/ml/models/race_lstm.onnx` for the API. Benchmark PyTorch vs ONNX on the target CPU/GPU before choosing it.

## Tests

Run backend tests from the repository root:

```bash
python -m pytest server/tests -q
```

Run simulation tests from the simulation folder (legacy tests import `simulation` as a top-level package):

```bash
cd simulation_environment
python -m pytest tests -q
```

Run frontend tests from `frontend/` with Node 22.16+:

```bash
npm test
```

## Security and production checklist

Before exposing this system outside a trusted development network, add authentication/authorization to simulation controls, dataset upload, model activation and collaboration rooms; TLS termination; request and upload quotas; persistent audit events; secret management; model/dataset retention policies; backup/restore; and dependency/image scanning. Do not expose Grafana with the default password.

The backend compares a matured one-step LSTM forecast with the next sampled actual position and exports its error histogram; this is a forecast-error signal, not a full statistical feature-distribution drift detector. The current Redis publisher emits `race:simulation:<session_id>` telemetry for downstream consumers. It does not yet coordinate a single live simulation across multiple API replicas. Keep API replicas at one until a distributed session owner, Redis subscriber/fan-out, sticky routing, and leader/fencing semantics are implemented and tested. Scale Celery/Ray offline workers independently.

The simulation's coordinate metadata explicitly says ETH-UCY-compatible coordinate units and does not claim physical metre calibration. Validate dataset FPS and coordinate calibration before interpreting times, velocities, density or evacuation-time results as real-world measurements.
