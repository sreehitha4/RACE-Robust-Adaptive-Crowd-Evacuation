from fastapi import APIRouter

from server.api import dataset_routes as datasets, ml_routes as ml

router = APIRouter()
router.include_router(datasets.router)
router.include_router(ml.router)
