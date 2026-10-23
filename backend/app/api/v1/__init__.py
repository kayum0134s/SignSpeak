"""
API v1 Router Aggregator
"""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.translate import router as translate_router
from backend.app.api.v1.signs import router as signs_router
from backend.app.api.v1.recognition import router as recognition_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.training import router as training_router
from backend.app.api.v1.models import router as models_router
from backend.app.api.v1.evaluation import router as evaluation_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(translate_router)
api_v1_router.include_router(signs_router)
api_v1_router.include_router(recognition_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(training_router)
api_v1_router.include_router(models_router)
api_v1_router.include_router(evaluation_router)
