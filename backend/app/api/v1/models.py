"""
Model Registry Endpoints.
Lists registered models, retrieves metadata, and manages active models.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.recognition_service import recognition_service
from ml.datasets.base import TaskType
from ml.registry.registry import LocalModelRegistry, RegisteredModelInfo

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/")
def list_models(task: Optional[str] = None):
    """Lists all registered models, optionally filtered by supported task."""
    registry = recognition_service.registry
    task_enum = TaskType(task) if task else None
    models = registry.list_models(task=task_enum)
    return [m.model_dump() for m in models]


@router.get("/{model_id}")
def get_model_details(model_id: str):
    """Retrieves metadata, training configs, and evaluation metrics for a specific model."""
    registry = recognition_service.registry
    info = registry.get_model_info(model_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
    return info.model_dump()


class SelectModelPayload(BaseModel):
    model_id: str
    task: str


@router.post("/select")
def select_active_model(payload: SelectModelPayload):
    """Sets active model for inference after asserting task compatibility."""
    try:
        task_enum = TaskType(payload.task)
        recognition_service.set_active_model(payload.model_id, task_enum)
        return {
            "status": "ok",
            "message": f"Model '{payload.model_id}' activated for task '{payload.task}'."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
