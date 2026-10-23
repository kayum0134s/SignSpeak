"""
Task A: Isolated Sign Recognition Model.
Predicts a single labeled ASL sign from a short video landmark sequence.
Uses Spatial-Temporal Feature Projection + BiGRU + Temporal Attention Pooling.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.datasets.base import TaskType
from ml.models.base import BaseSignModel
from ml.preprocessing.sequence import normalize_coordinates, resample_sequence
from ml.preprocessing.vocabulary import Vocabulary


class TemporalAttention(nn.Module):
    """Computes learned attention weights across the temporal dimension."""

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # x: (B, T, H)
        scores = self.attn(x)  # (B, T, 1)
        if mask is not None:
            scores = scores.masked_fill(~mask.unsqueeze(-1), -1e9)
        weights = F.softmax(scores, dim=1)  # (B, T, 1)
        context = torch.sum(x * weights, dim=1)  # (B, H)
        return context


class IsolatedSignClassifier(BaseSignModel):
    """
    Task A: Isolated ASL Word/Letter Classifier.
    Predicts a categorical sign label from a normalized sequence of 3D landmarks.
    """

    def __init__(
        self,
        model_id: str,
        num_classes: int,
        label_vocab: List[str],
        input_dim: int = 144,
        sequence_length: int = 30,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        super().__init__(model_id=model_id, task=TaskType.ISOLATED_SIGN)
        self.num_classes = num_classes
        self.label_vocab = list(label_vocab)
        self.input_dim = input_dim
        self.sequence_length = sequence_length
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout_rate = dropout

        # Spatial Feature Projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # Temporal Sequence Modeling (BiGRU)
        self.bigru = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Temporal Attention Pooling
        self.attention = TemporalAttention(hidden_dim * 2)

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes)
        )

        self.metadata = {
            "model_id": model_id,
            "architecture": "BiGRU_Attention_Classifier",
            "task": TaskType.ISOLATED_SIGN.value,
            "num_classes": num_classes,
            "label_vocab": self.label_vocab,
            "input_dim": input_dim,
            "sequence_length": sequence_length,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout
        }

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: (B, T, D) landmark tensor
            mask: Optional (B, T) boolean mask
        Returns:
            logits: (B, num_classes)
        """
        proj = self.input_proj(x)
        gru_out, _ = self.bigru(proj)  # (B, T, 2 * H)
        context = self.attention(gru_out, mask=mask)  # (B, 2 * H)
        logits = self.classifier(context)  # (B, num_classes)
        return logits

    def predict(
        self,
        sample_input: Union[np.ndarray, torch.Tensor],
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Inference on a single sequence of landmarks (T, 144).
        Resamples and normalizes input to model specifications.
        """
        self.eval()
        with torch.no_grad():
            if isinstance(sample_input, torch.Tensor):
                seq = sample_input.detach().cpu().numpy()
            else:
                seq = np.array(sample_input, dtype=np.float32)

            if seq.ndim == 3:
                # Batch of 1
                seq = seq[0]

            # Normalize & resample
            seq = normalize_coordinates(seq)
            resampled = resample_sequence(seq, target_len=self.sequence_length)

            tensor_in = torch.from_numpy(resampled).unsqueeze(0)  # (1, T, D)
            logits = self.forward(tensor_in)
            probs = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

            top_idx = int(np.argmax(probs))
            top_label = self.label_vocab[top_idx] if top_idx < len(self.label_vocab) else f"CLASS_{top_idx}"
            top_conf = float(probs[top_idx])

            k = min(top_k, len(self.label_vocab))
            top_k_indices = np.argsort(probs)[::-1][:k]
            top_k_results = [
                {
                    "label": self.label_vocab[idx] if idx < len(self.label_vocab) else f"CLASS_{idx}",
                    "confidence": round(float(probs[idx]), 4)
                }
                for idx in top_k_indices
            ]

            return {
                "top_prediction": top_label,
                "confidence": round(top_conf, 4),
                "top_k": top_k_results,
                "all_probabilities": {
                    self.label_vocab[i]: round(float(probs[i]), 4)
                    for i in range(len(self.label_vocab))
                }
            }

    @classmethod
    def load_checkpoint(cls, checkpoint_path: Path, device: str = "cpu") -> "IsolatedSignClassifier":
        payload = torch.load(checkpoint_path, map_location=device)
        meta = payload["metadata"]

        model = cls(
            model_id=meta.get("model_id", payload.get("model_id", "isolated_model")),
            num_classes=meta["num_classes"],
            label_vocab=meta["label_vocab"],
            input_dim=meta.get("input_dim", 144),
            sequence_length=meta.get("sequence_length", 30),
            hidden_dim=meta.get("hidden_dim", 128),
            num_layers=meta.get("num_layers", 2),
            dropout=meta.get("dropout", 0.3)
        )
        model.load_state_dict(payload["state_dict"])
        model.to(device)
        model.eval()
        return model
