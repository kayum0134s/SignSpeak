"""
Base model interface and model metadata specifications for SignSpeak.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import torch
import torch.nn as nn
from ml.datasets.base import TaskType


class BaseSignModel(nn.Module, ABC):
    """
    Abstract interface for all SignSpeak neural models.
    Guarantees standard prediction interfaces, checkpoint saving/loading,
    and task compatibility contracts.
    """

    def __init__(self, model_id: str, task: TaskType):
        super().__init__()
        self.model_id = model_id
        self.task = task
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def forward(self, x: torch.Tensor, *args, **kwargs) -> torch.Tensor:
        """PyTorch forward pass."""
        pass

    @abstractmethod
    def predict(self, sample_input: Any) -> Dict[str, Any]:
        """
        Inference interface accepting raw or preprocessed inputs and returning
        structured prediction dictionary with confidence scores.
        """
        pass

    def save_checkpoint(
        self,
        checkpoint_path: Path,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Saves PyTorch state dict and model configuration metadata."""
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        meta = {**self.metadata, **(extra_metadata or {})}
        payload = {
            "model_id": self.model_id,
            "task": self.task.value,
            "state_dict": self.state_dict(),
            "metadata": meta
        }
        torch.save(payload, checkpoint_path)

    @classmethod
    @abstractmethod
    def load_checkpoint(cls, checkpoint_path: Path, device: str = "cpu") -> "BaseSignModel":
        """Loads model from checkpoint."""
        pass
