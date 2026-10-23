"""
Webcam Real-time Recognition Endpoints.
Processes frame landmarks, manages live transcripts, and reports model status.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.recognition_service import recognition_service
from ml.datasets.base import TaskType

router = APIRouter(prefix="/recognition", tags=["Recognition"])


class FrameLandmarksPayload(BaseModel):
    landmarks: List[float] = Field(..., description="Array of 144 float landmark coordinates for the current frame")
    timestamp: Optional[float] = Field(None, description="Client frame capture timestamp in ms or seconds")


class ModelSelectPayload(BaseModel):
    model_id: str
    task: str = Field(..., description="isolated_sign, continuous_gloss, or sentence_translation")


@router.get("/status")
def get_recognition_status():
    """Returns current active model, task compatibility, and live transcript state."""
    return recognition_service.get_status()


@router.post("/process_frame")
def process_frame(payload: FrameLandmarksPayload):
    """
    Receives extracted landmarks for a single webcam frame.
    Processes within bounded sliding buffer and returns transcript update.
    Never persists video frames to disk.
    """
    return recognition_service.process_frame_landmarks(
        landmarks=payload.landmarks,
        timestamp=payload.timestamp
    )


@router.post("/reset")
def reset_transcript():
    """Resets the live transcript buffer and confidence trackers."""
    recognition_service.reset_transcript()
    return {"status": "ok", "message": "Transcript and frame buffers reset."}


@router.post("/select_model")
def select_model(payload: ModelSelectPayload):
    """Switches the active recognition model for live webcam inference."""
    try:
        task_enum = TaskType(payload.task)
        recognition_service.set_active_model(payload.model_id, task_enum)
        return {
            "status": "ok",
            "message": f"Active model set to '{payload.model_id}' for task '{payload.task}'.",
            "model_id": payload.model_id,
            "task": payload.task
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
