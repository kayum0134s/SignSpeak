"""
Temporal Sequence Preprocessing and Coordinate Normalization.
Normalizes landmark arrays to fixed sequence lengths via linear interpolation
or padding, and normalizes coordinates relative to bodily references.
"""

from typing import Optional
import numpy as np


def resample_sequence(
    sequence: np.ndarray,
    target_len: int = 30
) -> np.ndarray:
    """
    Resamples a temporal sequence (T, D) to (target_len, D) using linear interpolation.
    Handles T < target_len (upsampling) and T > target_len (downsampling).
    """
    t_len, d_dim = sequence.shape
    if t_len == target_len:
        return sequence.astype(np.float32)

    if t_len == 1:
        # Repeat single frame
        return np.repeat(sequence, target_len, axis=0).astype(np.float32)

    orig_indices = np.linspace(0, t_len - 1, num=t_len)
    target_indices = np.linspace(0, t_len - 1, num=target_len)

    resampled = np.zeros((target_len, d_dim), dtype=np.float32)
    for d in range(d_dim):
        resampled[:, d] = np.interp(target_indices, orig_indices, sequence[:, d])

    return resampled


def pad_or_truncate_sequence(
    sequence: np.ndarray,
    max_len: int = 60,
    pad_value: float = 0.0
) -> tuple[np.ndarray, np.ndarray]:
    """
    Pads or truncates a sequence to max_len.
    Returns:
        res: np.ndarray of shape (max_len, D)
        mask: np.ndarray of shape (max_len,) boolean mask (True for real frames)
    """
    t_len, d_dim = sequence.shape
    if t_len >= max_len:
        return sequence[:max_len].astype(np.float32), np.ones(max_len, dtype=bool)

    padded = np.full((max_len, d_dim), pad_value, dtype=np.float32)
    padded[:t_len] = sequence
    mask = np.zeros(max_len, dtype=bool)
    mask[:t_len] = True
    return padded, mask


Tuple_Sequence = tuple[np.ndarray, np.ndarray]


def normalize_coordinates(sequence: np.ndarray) -> np.ndarray:
    """
    Center coordinates relative to upper pose shoulders or wrist landmarks
    and normalize scale to prevent signer distance variation.
    Sequence shape: (T, 144).
    """
    seq = sequence.copy()
    # Left shoulder index: 126 (x), 127 (y), 128 (z)
    # Right shoulder index: 129 (x), 130 (y), 131 (z)
    for t in range(seq.shape[0]):
        l_sh = seq[t, 126:129]
        r_sh = seq[t, 129:132]

        if np.any(l_sh) and np.any(r_sh):
            # Center of shoulders
            center = (l_sh + r_sh) / 2.0
            dist = np.linalg.norm(l_sh - r_sh)
            scale = dist if dist > 0.05 else 1.0

            # Normalize hands and pose
            # Hands: 0:126
            for i in range(0, 126, 3):
                if np.any(seq[t, i:i + 3]):
                    seq[t, i:i + 3] = (seq[t, i:i + 3] - center) / scale
            # Pose: 126:144
            for i in range(126, 144, 3):
                if np.any(seq[t, i:i + 3]):
                    seq[t, i:i + 3] = (seq[t, i:i + 3] - center) / scale

    return seq.astype(np.float32)
