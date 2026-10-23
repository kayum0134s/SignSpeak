"""
Training Configuration Schemas.
Enforces type validation, reasonable hyperparameter ranges,
and prevents invalid task combinations before training jobs begin.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from ml.datasets.base import TaskType


class TrainingConfig(BaseModel):
    """Configuration specification for model training."""
    task: str = Field(..., description="Target task: isolated_sign, continuous_gloss, or sentence_translation")
    model_id: str = Field(..., description="Unique model identifier and registration handle")
    dataset_adapter: str = Field(..., description="Adapter name: how2sign, wlasl, ms-asl, or custom")
    manifest_path: str = Field(..., description="Path to input dataset manifest JSON file")
    checkpoint_dir: str = Field("checkpoints", description="Directory to store model checkpoints")
    
    # Architecture
    model_architecture: str = Field("BiGRU_Attention", description="Architecture identifier")
    input_dim: int = Field(144, ge=24, le=1024, description="Input landmark feature dimension")
    sequence_length: int = Field(30, ge=5, le=300, description="Normalized sequence frame count")
    hidden_dim: int = Field(128, ge=16, le=1024, description="Hidden state dimension")
    num_layers: int = Field(2, ge=1, le=8, description="Number of recurrent or transformer layers")
    dropout: float = Field(0.3, ge=0.0, le=0.8, description="Dropout probability")

    # Optimization
    batch_size: int = Field(16, ge=1, le=256, description="Training batch size")
    epochs: int = Field(10, ge=1, le=500, description="Maximum training epochs")
    learning_rate: float = Field(0.001, gt=0.0, le=0.1, description="Initial learning rate")
    weight_decay: float = Field(1e-4, ge=0.0, le=0.1, description="L2 weight decay")
    patience: int = Field(5, ge=1, le=50, description="Early stopping patience")
    random_seed: int = Field(42, description="Random seed for reproducibility")
    device: str = Field("cpu", description="Execution device: cpu or cuda")

    # Extra
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("task")
    @classmethod
    def validate_task(cls, v: str) -> str:
        clean = v.lower().strip()
        valid = {t.value for t in TaskType}
        if clean not in valid:
            raise ValueError(f"Invalid task '{v}'. Supported tasks: {sorted(list(valid))}")
        return clean

    def save(self, config_path: Path) -> None:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, config_path: Path) -> "TrainingConfig":
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
