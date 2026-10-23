"""
Training Job Endpoints.
Allows launching, monitoring, and cancelling ML training jobs.
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from backend.app.services.training_service import training_service
from ml.training.config import TrainingConfig

router = APIRouter(prefix="/training", tags=["Training"])


@router.post("/start")
def start_training(config_data: Dict[str, Any]):
    """
    Validates training configuration and starts background training job.
    Enforces concurrency limit (max 1 job at a time).
    """
    try:
        config = TrainingConfig.model_validate(config_data)
        job = training_service.start_training_job(config)
        return {
            "status": "started",
            "job_id": job.job_id,
            "message": f"Training job '{job.job_id}' started for task '{config.task}'."
        }
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
def get_training_status():
    """Returns real-time status, logs, metrics, and progress of the current or most recent job."""
    return training_service.get_current_job_status()


@router.post("/cancel")
def cancel_training():
    """Cancels the active training job safely."""
    return training_service.cancel_training_job()
