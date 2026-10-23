"""
Task B: Continuous Sign Language Gloss Recognition Model.
Uses Connectionist Temporal Classification (CTC) with Bidirectional Recurrent Neural Networks.
Decodes unaligned continuous signing streams into sequences of discrete ASL glosses.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.datasets.base import TaskType
from ml.models.base import BaseSignModel
from ml.preprocessing.sequence import normalize_coordinates
from ml.preprocessing.vocabulary import Vocabulary


class ContinuousGlossRecognizer(BaseSignModel):
    """
    Temporal sequence model trained with CTC loss to predict variable-length
    gloss sequences from continuous landmark streams.
    """

    def __init__(
        self,
        model_id: str,
        gloss_vocab: List[str],
        input_dim: int = 144,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3
    ):
        super().__init__(model_id=model_id, task=TaskType.CONTINUOUS_GLOSS)
        
        # Build CTC vocabulary where index 0 is <blank>
        self.gloss_vocab_raw = list(gloss_vocab)
        self.vocab = Vocabulary(self.gloss_vocab_raw, ctc_mode=True)
        self.num_classes = len(self.vocab)  # num glosses + 1 (<blank>)
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Spatial Feature Projection
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout)
        )

        # Temporal Sequence Modeling
        self.recurrent = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # Frame-wise Gloss Projection
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, self.num_classes)
        )

        self.metadata = {
            "model_id": model_id,
            "architecture": "BiGRU_CTC_GlossRecognizer",
            "task": TaskType.CONTINUOUS_GLOSS.value,
            "num_classes": self.num_classes,
            "gloss_vocab": self.gloss_vocab_raw,
            "input_dim": input_dim,
            "hidden_dim": hidden_dim,
            "num_layers": num_layers,
            "dropout": dropout
        }

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        Args:
            x: (B, T, D) continuous landmark tensor
        Returns:
            log_probs: (T, B, num_classes) required format for nn.CTCLoss
        """
        proj = self.input_proj(x)
        out, _ = self.recurrent(proj)  # (B, T, 2 * H)
        logits = self.fc(out)          # (B, T, num_classes)
        log_probs = F.log_softmax(logits, dim=-1).transpose(0, 1)  # (T, B, num_classes)
        return log_probs

    def decode_ctc(self, log_probs: torch.Tensor) -> List[List[str]]:
        """
        Greedy CTC decoding:
        Argmax per frame -> collapse adjacent duplicate tokens -> remove <blank> (index 0).
        log_probs shape: (T, B, num_classes)
        """
        # (T, B, num_classes) -> (B, T)
        best_paths = torch.argmax(log_probs, dim=-1).transpose(0, 1).cpu().numpy()
        results: List[List[str]] = []

        for b in range(best_paths.shape[0]):
            path = best_paths[b]
            collapsed: List[int] = []
            prev_token = None

            for token_id in path:
                if token_id != prev_token:
                    collapsed.append(token_id)
                    prev_token = token_id

            # Filter out blank index (0)
            glosses = [
                self.vocab.get_token(idx)
                for idx in collapsed
                if idx != self.vocab.blank_id and idx < len(self.vocab)
            ]
            results.append(glosses)

        return results

    def predict(self, sample_input: Union[np.ndarray, torch.Tensor]) -> Dict[str, Any]:
        """
        Inference on continuous sequence of landmarks (T, 144).
        Decodes into predicted gloss sequence.
        """
        self.eval()
        with torch.no_grad():
            if isinstance(sample_input, torch.Tensor):
                seq = sample_input.detach().cpu().numpy()
            else:
                seq = np.array(sample_input, dtype=np.float32)

            if seq.ndim == 3:
                seq = seq[0]

            seq = normalize_coordinates(seq)
            tensor_in = torch.from_numpy(seq).unsqueeze(0).float()  # (1, T, D)
            log_probs = self.forward(tensor_in)  # (T, 1, num_classes)

            decoded = self.decode_ctc(log_probs)[0]
            confidence_mean = float(torch.exp(log_probs).max(dim=-1).values.mean().item())

            return {
                "gloss_sequence": decoded,
                "gloss_text": " ".join(decoded),
                "confidence": round(confidence_mean, 4),
                "frame_count": int(seq.shape[0]),
                "detected_gloss_count": len(decoded)
            }

    @classmethod
    def load_checkpoint(cls, checkpoint_path: Path, device: str = "cpu") -> "ContinuousGlossRecognizer":
        payload = torch.load(checkpoint_path, map_location=device)
        meta = payload["metadata"]

        model = cls(
            model_id=meta.get("model_id", "continuous_gloss_model"),
            gloss_vocab=meta["gloss_vocab"],
            input_dim=meta.get("input_dim", 144),
            hidden_dim=meta.get("hidden_dim", 128),
            num_layers=meta.get("num_layers", 2),
            dropout=meta.get("dropout", 0.3)
        )
        model.load_state_dict(payload["state_dict"])
        model.to(device)
        model.eval()
        return model
