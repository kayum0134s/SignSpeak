"""
Local Model Registry and Checkpoint Verification Service.
Tracks registered models, architectures, task compatibility, SHA-256 checksums,
and evaluation metrics while preventing corrupted or incompatible models from loading.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from ml.datasets.base import TaskType
from ml.models.base import BaseSignModel
from ml.models.continuous_seq2seq import ContinuousGlossRecognizer
from ml.models.isolated_classifier import IsolatedSignClassifier
from ml.models.translation_pipeline import SignTranslationPipeline


class IncompatibleTaskError(ValueError):
    """Raised when an attempt is made to load a model for an unsupported task."""
    pass


class CheckpointVerificationError(RuntimeError):
    """Raised when checkpoint file is missing or its SHA-256 checksum is corrupted."""
    pass


class RegisteredModelInfo(BaseModel):
    """Declarative metadata specification for registered models."""
    model_id: str
    version: str = "1.0.0"
    task: str = Field(..., description="isolated_sign, continuous_gloss, or sentence_translation")
    sign_language: str = "ASL"
    dataset_sources: List[str] = Field(default_factory=list)
    dataset_versions: List[str] = Field(default_factory=list)
    vocabulary: List[str] = Field(default_factory=list)
    num_classes: int
    preprocessing: Dict[str, Any] = Field(default_factory=dict)
    architecture: str
    checkpoint_path: str
    checksum_sha256: str
    training_config: Optional[Dict[str, Any]] = None
    evaluation_metrics: Optional[Dict[str, Any]] = None
    license_info: str = ""
    attribution: str = ""
    known_limitations: List[str] = Field(default_factory=list)
    registered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active_for_task: bool = False


class LocalModelRegistry:
    """Manages model artifacts, metadata registries, and active deployment targets."""

    def __init__(self, registry_dir: Optional[Path] = None):
        if registry_dir is None:
            # Default to <project_root>/ml/registry_data
            registry_dir = Path(__file__).resolve().parent / "registry_data"
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.registry_dir / "models.json"
        self.active_file = self.registry_dir / "active_models.json"

        if not self.metadata_file.exists():
            self._save_all({})
        if not self.active_file.exists():
            self._save_active({})

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        if not self.metadata_file.exists():
            return {}
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_active(self) -> Dict[str, str]:
        if not self.active_file.exists():
            return {}
        try:
            with open(self.active_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_active(self, active: Dict[str, str]) -> None:
        with open(self.active_file, "w", encoding="utf-8") as f:
            json.dump(active, f, indent=2)

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Computes SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def register_model(
        self,
        info: RegisteredModelInfo,
        verify_checkpoint: bool = True
    ) -> RegisteredModelInfo:
        """Registers model checkpoint and metadata."""
        ckpt_path = Path(info.checkpoint_path)
        if not ckpt_path.is_absolute():
            ckpt_path = self.registry_dir / ckpt_path

        if verify_checkpoint:
            if not ckpt_path.exists():
                raise FileNotFoundError(f"Checkpoint file not found: {ckpt_path}")
            current_hash = self.calculate_sha256(ckpt_path)
            if info.checksum_sha256 and info.checksum_sha256 != current_hash:
                raise CheckpointVerificationError(
                    f"Checksum mismatch for {ckpt_path}. Expected {info.checksum_sha256}, got {current_hash}"
                )
            info.checksum_sha256 = current_hash

        models = self._load_all()
        models[info.model_id] = info.model_dump()
        self._save_all(models)

        # Set as active for task if first registered for task
        active = self._load_active()
        if info.task not in active:
            self.set_active_model(info.model_id, TaskType(info.task))

        return info

    def get_model_info(self, model_id: str) -> Optional[RegisteredModelInfo]:
        models = self._load_all()
        if model_id in models:
            return RegisteredModelInfo.model_validate(models[model_id])
        return None

    def list_models(self, task: Optional[Union[str, TaskType]] = None) -> List[RegisteredModelInfo]:
        models = self._load_all()
        task_filter = task.value if isinstance(task, TaskType) else task
        result = []
        active = self._load_active()

        for mid, mdata in models.items():
            info = RegisteredModelInfo.model_validate(mdata)
            info.is_active_for_task = (active.get(info.task) == info.model_id)
            if task_filter is None or info.task == task_filter:
                result.append(info)
        return result

    def assert_task_compatibility(self, model_id: str, required_task: TaskType) -> RegisteredModelInfo:
        """Validates that model supports the requested task."""
        info = self.get_model_info(model_id)
        if not info:
            raise KeyError(f"Model '{model_id}' is not registered.")
        if info.task != required_task.value:
            raise IncompatibleTaskError(
                f"Model '{model_id}' supports task '{info.task}', which is incompatible with requested task '{required_task.value}'."
            )
        return info

    def set_active_model(self, model_id: str, task: TaskType) -> None:
        """Sets the default model to use for a given task."""
        self.assert_task_compatibility(model_id, task)
        active = self._load_active()
        active[task.value] = model_id
        self._save_active(active)

    def get_active_model(self, task: TaskType) -> Optional[RegisteredModelInfo]:
        active = self._load_active()
        mid = active.get(task.value)
        if mid:
            return self.get_model_info(mid)
        # Fallback to any model with matching task
        candidates = self.list_models(task=task)
        return candidates[0] if candidates else None

    def load_model_instance(self, model_id: str, device: str = "cpu") -> BaseSignModel:
        """Loads and returns the instantiated PyTorch model for inference."""
        info = self.get_model_info(model_id)
        if not info:
            raise KeyError(f"Model '{model_id}' is not registered.")

        ckpt_path = Path(info.checkpoint_path)
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Checkpoint file missing: {ckpt_path}")

        # Verify checksum
        current_hash = self.calculate_sha256(ckpt_path)
        if info.checksum_sha256 and current_hash != info.checksum_sha256:
            raise CheckpointVerificationError(f"Corrupted checkpoint detected for model '{model_id}'!")

        if info.task == TaskType.ISOLATED_SIGN.value:
            return IsolatedSignClassifier.load_checkpoint(ckpt_path, device=device)
        elif info.task == TaskType.CONTINUOUS_GLOSS.value:
            return ContinuousGlossRecognizer.load_checkpoint(ckpt_path, device=device)
        elif info.task == TaskType.SENTENCE_TRANSLATION.value:
            return SignTranslationPipeline.load_checkpoint(ckpt_path, device=device)
        else:
            raise ValueError(f"Unsupported model task type: {info.task}")
