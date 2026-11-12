# RACE Phase 2: Dataset Ingestion and Model Registry

## Implemented now

- Dataset CSV upload with generated server-side IDs (client filenames are metadata only).
- Upload size and row limits.
- Streaming file writes, SHA-256 digest, UTF-8 CSV validation, finite numeric checks.
- Atomic move from temporary upload to final dataset path.
- Dataset listing and dataset-ID path lookup.
- Versioned `.pth` model listing.
- Candidate predictor construction before activation.
- Atomic persisted active-model pointer (`active_model.json`).
- Failed candidate loads preserve the previous in-memory active model.
- FastAPI lifespan initialization and shutdown.
- Routes:
  - `POST /api/v1/datasets/upload`
  - `GET /api/v1/datasets`
  - `GET /api/v1/ml/models`
  - `POST /api/v1/ml/models/{model_id}/activate`

## Important limitations (intentional)

1. Dataset format is currently a documented normalized CSV contract:
   `pedestrian_id,frame,x,y`. ETH/UCY raw files must be converted into this schema first.
2. Model activation uses `RACEPredictor` from `ml/model_inference.py`. A compatible `.pth` checkpoint and PyTorch must be installed for the default loader to work.
3. No retraining endpoint is exposed yet. We must not return fake "completed" jobs. A real training worker requires Sreehitha's training entry point, configuration contract, and output checkpoint format.
4. The active model pointer is process-local for inference and persisted on disk for restart recovery. For multi-worker deployments, use a shared model-serving process or coordinated registry backend; do not assume process memory is shared.
5. Add authentication/authorization before exposing uploads or model activation beyond a trusted development network.

## Run

From repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r server\requirements.txt
python -m pytest server\tests -q
python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs`.

## Upload example

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/datasets/upload" `
  -F "file=@.\sample-trajectories.csv"
```

Expected CSV header:

```csv
pedestrian_id,frame,x,y
1,0,1.0,2.0
1,1,1.2,2.1
```

## Model registry

Place compatible checkpoints in `ml/weights/`, for example `trajectory_v1.pth`.
List with `GET /api/v1/ml/models`, then activate using:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/ml/models/trajectory_v1.pth/activate"
```

The registry validates by constructing the actual `RACEPredictor` before switching the active pointer.
