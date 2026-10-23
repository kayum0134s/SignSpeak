"""
Dataset Discovery and Validation Endpoints.
Allows users to inspect local datasets, validate annotations,
detect signer leakage, and generate training manifests.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.utils.config import PROJECT_ROOT
from ml.datasets import (
    get_adapter,
    list_adapters,
)
from ml.datasets.base import TaskType

router = APIRouter(prefix="/datasets", tags=["Datasets"])


class ValidateDatasetPayload(BaseModel):
    adapter: str = Field(..., description="Adapter name: custom, how2sign, wlasl, ms-asl")
    dataset_path: str = Field(..., description="Path to local dataset directory (relative to workspace or absolute)")


class CreateManifestPayload(BaseModel):
    adapter: str
    dataset_path: str
    manifest_name: str = Field("manifest.json", description="Filename for manifest inside data/manifests/")
    task: Optional[str] = None


@router.get("/adapters")
def get_adapters():
    """Lists all supported dataset adapters and their descriptions."""
    names = list_adapters()
    results = []
    for name in names:
        try:
            adapter = get_adapter(name)
            results.append({
                "name": adapter.name,
                "version": adapter.version,
                "source": adapter.source,
                "license": adapter.license_info,
                "attribution": adapter.attribution,
                "annotation_type": adapter.annotation_type.value,
                "modalities": adapter.modalities,
                "supported_tasks": [t.value for t in adapter.supported_tasks]
            })
        except Exception:
            pass
    return results


@router.post("/validate")
def validate_dataset(payload: ValidateDatasetPayload):
    """
    Validates a dataset directory against the adapter contract.
    Checks file existence, formats, sample counts, and signer leakage without running heavy downloads.
    """
    try:
        adapter = get_adapter(payload.adapter)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    root_dir = Path(payload.dataset_path)
    if not root_dir.is_absolute():
        root_dir = PROJECT_ROOT / root_dir

    report = adapter.validate(root_dir)
    return report.model_dump()


@router.post("/create_manifest")
def create_manifest(payload: CreateManifestPayload):
    """Discovers samples and writes a versioned manifest to data/manifests/."""
    try:
        adapter = get_adapter(payload.adapter)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    root_dir = Path(payload.dataset_path)
    if not root_dir.is_absolute():
        root_dir = PROJECT_ROOT / root_dir

    if not root_dir.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {root_dir}")

    manifest_dir = PROJECT_ROOT / "data" / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / payload.manifest_name

    task_enum = TaskType(payload.task) if payload.task else None
    manifest = adapter.generate_manifest(root_dir, output_path=manifest_path, task=task_enum)

    return {
        "status": "ok",
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "total_samples": manifest.total_samples,
        "splits": manifest.splits,
        "vocab_size": len(manifest.label_vocab),
        "task": manifest.task
    }


@router.get("/manifests")
def list_manifests():
    """Lists all generated manifests in data/manifests/."""
    manifest_dir = PROJECT_ROOT / "data" / "manifests"
    if not manifest_dir.exists():
        return []

    manifests = []
    for mf in manifest_dir.glob("*.json"):
        try:
            import json
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            manifests.append({
                "filename": mf.name,
                "relative_path": str(mf.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "dataset_name": data.get("dataset_name"),
                "task": data.get("task"),
                "total_samples": data.get("total_samples"),
                "splits": data.get("splits"),
                "vocab_size": len(data.get("label_vocab", []))
            })
        except Exception:
            pass
    return manifests
