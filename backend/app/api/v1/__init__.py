"""
API v1 Router Aggregator
"""

from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.translate import router as translate_router
from backend.app.api.v1.signs import router as signs_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(translate_router)
api_v1_router.include_router(signs_router)
