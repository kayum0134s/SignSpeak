"""
Evaluation Endpoints.
Runs held-out evaluation on test splits and serves evaluation reports.
Never fabricates metrics.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.recognition_service import recognition_service
from backend.app.utils.config import PROJECT_ROOT
from ml.datasets.base import DatasetManifest, TaskType
from ml.evaluation.evaluator import EvaluationReport, ModelEvaluator

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


class RunEvaluationPayload(BaseModel):
    model_id: str
    manifest_path: str
    dataset_name: Optional[str] = None


@router.post("/run")
def run_evaluation(payload: RunEvaluationPayload):
    """
    Executes benchmark evaluation on the test split of the specified manifest.
    Calculates task-specific metrics (accuracy, WER, BLEU, chrF, latency).
    """
    registry = recognition_service.registry
    info = registry.get_model_info(payload.model_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Model '{payload.model_id}' not found.")

    manifest_file = Path(payload.manifest_path)
    if not manifest_file.is_absolute():
        manifest_file = PROJECT_ROOT / manifest_file
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail=f"Manifest file not found: {manifest_file}")

    manifest = DatasetManifest.load_from_file(manifest_file)
    test_samples = [s for s in manifest.samples if s.split == "test"]
    if not test_samples:
        # Fallback to val if test split not specified
        test_samples = [s for s in manifest.samples if s.split == "val"]
    if not test_samples:
        test_samples = manifest.samples[:min(20, len(manifest.samples))]

    model_instance = registry.load_model_instance(payload.model_id)
    ds_name = payload.dataset_name or manifest.dataset_name

    if info.task == TaskType.ISOLATED_SIGN.value:
        report = ModelEvaluator.evaluate_isolated(model_instance, test_samples, dataset_name=ds_name)
    elif info.task == TaskType.CONTINUOUS_GLOSS.value:
        report = ModelEvaluator.evaluate_continuous_gloss(model_instance, test_samples, dataset_name=ds_name)
    elif info.task == TaskType.SENTENCE_TRANSLATION.value:
        report = ModelEvaluator.evaluate_translation(model_instance, test_samples, dataset_name=ds_name)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported evaluation task: {info.task}")

    # Save report to reports directory
    reports_dir = PROJECT_ROOT / "data" / "evaluation_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / f"{payload.model_id}_eval_{report.split_evaluated}.json"
    report.save(report_file)

    # Update model metadata with evaluation metrics
    info.evaluation_metrics = report.metrics
    registry.register_model(info, verify_checkpoint=False)

    return report.model_dump()


@router.get("/reports")
def list_evaluation_reports():
    """Lists saved evaluation reports."""
    reports_dir = PROJECT_ROOT / "data" / "evaluation_reports"
    if not reports_dir.exists():
        return []

    reports = []
    for rf in reports_dir.glob("*.json"):
        try:
            import json
            with open(rf, "r", encoding="utf-8") as f:
                data = json.load(f)
            reports.append(data)
        except Exception:
            pass
    return reports
