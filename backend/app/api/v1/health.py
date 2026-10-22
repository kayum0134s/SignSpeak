"""
Health Check & Status Endpoint
"""

import time
from fastapi import APIRouter
from backend.app.models.schemas import HealthResponse
from backend.app.services.translator_service import translator_service
from backend.app.utils.config import ENVIRONMENT

router = APIRouter(tags=["Health"])
START_TIME = time.time()

@router.get("/health", response_model=HealthResponse)
def get_health():
    """Retrieve operational status, uptime, and lexicon stats."""
    uptime = time.time() - START_TIME
    stats = translator_service.get_stats()

    return HealthResponse(
        status="healthy",
        version="2.0.0",
        environment=ENVIRONMENT,
        uptime_seconds=round(uptime, 2),
        total_asl_signs=stats["total_asl_signs"],
        total_isl_signs=stats["total_isl_signs"]
    )
