"""RACE FastAPI orchestration service."""
import logging
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from server.api.routes import router
from server.api.dataset_routes import router as dataset_router
from server.api.ml_routes import router as ml_router
from server.api.distributed_routes import router as distributed_router
from server.api.job_routes import router as job_router
from server.services.dataset_service import DatasetService
from server.services.model_registry import ModelRegistry
from server.core.runtime import SimulationRuntime
from server.observability.metrics import HTTP_LATENCY, HTTP_REQUESTS
from server.observability.tracing import configure_tracing

logging.basicConfig(level=os.getenv("RACE_LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("race")

@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime = SimulationRuntime()
    app.state.runtime = runtime
    app.state.dataset_service = DatasetService()
    app.state.model_registry = ModelRegistry(SIM_MODEL_DIR)
    app.state.ray_jobs = {}
    await runtime.telemetry.start()
    logger.info("RACE backend started; ml_enabled=%s redis_enabled=%s",
                runtime.simulation.ml.enabled, bool(runtime.telemetry.client))
    try:
        yield
    finally:
        await runtime.shutdown()

SIM_MODEL_DIR = __import__("pathlib").Path(__file__).resolve().parents[1] / "simulation_environment" / "ml" / "models"
app = FastAPI(title="RACE API", version="2.0.0", lifespan=lifespan)
app.include_router(router)
app.include_router(dataset_router)
app.include_router(ml_router)
app.include_router(distributed_router)
app.include_router(job_router)

@app.middleware("http")
async def request_metrics(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    # Avoid high-cardinality paths in production metrics.
    if path.startswith("/api/simulation/"):
        path = "/api/simulation/{action}"
    HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
    HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response

@app.get("/metrics", include_in_schema=False)
async def metrics():
    payload = generate_latest()
    return Response(payload, media_type=CONTENT_TYPE_LATEST)

configure_tracing(app)
