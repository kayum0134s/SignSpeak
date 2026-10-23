"""
Tests for Phase 4: Isolated Sign Classification, Training Loop, and Evaluator.
"""

from pathlib import Path
import numpy as np
import pytest
import torch

from ml.datasets.base import NormalizedSample, TaskType
from ml.evaluation.evaluator import ModelEvaluator
from ml.evaluation.metrics import compute_isolated_metrics
from ml.models.isolated_classifier import IsolatedSignClassifier
from ml.preprocessing.sequence import (
    normalize_coordinates,
    pad_or_truncate_sequence,
    resample_sequence,
)
from ml.preprocessing.vocabulary import Vocabulary
from ml.training.config import TrainingConfig
from ml.training.trainer import IsolatedSignDataset, IsolatedSignTrainer


def test_sequence_resampling():
    # Downsample from 50 to 30 frames
    seq_50 = np.random.randn(50, 144).astype(np.float32)
    res_30 = resample_sequence(seq_50, target_len=30)
    assert res_30.shape == (30, 144)

    # Upsample from 10 to 30 frames
    seq_10 = np.random.randn(10, 144).astype(np.float32)
    res_up = resample_sequence(seq_10, target_len=30)
    assert res_up.shape == (30, 144)

    # Single frame repeat
    seq_1 = np.ones((1, 144), dtype=np.float32)
    res_1 = resample_sequence(seq_1, target_len=30)
    assert res_1.shape == (30, 144)
    assert np.all(res_1 == 1.0)


def test_pad_or_truncate():
    seq = np.ones((20, 144), dtype=np.float32)
    padded, mask = pad_or_truncate_sequence(seq, max_len=30)
    assert padded.shape == (30, 144)
    assert mask.sum() == 20
    assert not mask[25]


def test_vocabulary_encoding():
    vocab = Vocabulary(["HELLO", "WORLD", "THANK_YOU"])
    assert len(vocab) == 3
    assert vocab.get_id("HELLO") == 0
    assert vocab.get_token(1) == "WORLD"

    encoded = vocab.encode(["HELLO", "THANK_YOU"])
    assert encoded == [0, 2]
    decoded = vocab.decode(encoded)
    assert decoded == ["HELLO", "THANK_YOU"]


def test_isolated_classifier_forward_and_predict():
    labels = ["HELLO", "THANK_YOU", "YES", "NO"]
    model = IsolatedSignClassifier(
        model_id="test_model_v1",
        num_classes=len(labels),
        label_vocab=labels,
        input_dim=144,
        sequence_length=30,
        hidden_dim=32,
        num_layers=1
    )

    batch_x = torch.randn(2, 30, 144)
    logits = model(batch_x)
    assert logits.shape == (2, 4)

    # Test single-sequence prediction
    sample_seq = np.random.randn(25, 144).astype(np.float32)
    pred = model.predict(sample_seq)
    assert "top_prediction" in pred
    assert pred["top_prediction"] in labels
    assert "confidence" in pred
    assert 0.0 <= pred["confidence"] <= 1.0
    assert len(pred["top_k"]) == 4


def test_isolated_training_loop(tmp_path: Path):
    labels = ["HELLO", "THANK_YOU", "YES"]
    vocab = Vocabulary(labels)

    # Generate synthetic training and val samples
    train_samples = [
        NormalizedSample(sample_id=f"train_{i}", video_path=f"vid_{i}.mp4", task="isolated_sign", label=labels[i % 3], split="train")
        for i in range(12)
    ]
    val_samples = [
        NormalizedSample(sample_id=f"val_{i}", video_path=f"vid_{i}.mp4", task="isolated_sign", label=labels[i % 3], split="val")
        for i in range(6)
    ]

    train_ds = IsolatedSignDataset(train_samples, vocab, sequence_length=15, input_dim=48)
    val_ds = IsolatedSignDataset(val_samples, vocab, sequence_length=15, input_dim=48)

    model = IsolatedSignClassifier(
        model_id="smoke_train_model",
        num_classes=3,
        label_vocab=labels,
        input_dim=48,
        sequence_length=15,
        hidden_dim=16,
        num_layers=1
    )

    config = TrainingConfig(
        task="isolated_sign",
        model_id="smoke_train_model",
        dataset_adapter="custom",
        manifest_path=str(tmp_path / "manifest.json"),
        checkpoint_dir=str(tmp_path / "checkpoints"),
        input_dim=48,
        sequence_length=15,
        hidden_dim=16,
        num_layers=1,
        batch_size=4,
        epochs=3,
        learning_rate=0.01,
        device="cpu"
    )

    trainer = IsolatedSignTrainer(config, model, train_ds, val_ds)
    result = trainer.train()

    assert result["status"] == "completed"
    assert result["total_epochs"] == 3
    assert len(trainer.history) == 3
    best_ckpt = Path(result["checkpoint_path"])
    assert best_ckpt.exists()

    # Load saved checkpoint
    reloaded_model = IsolatedSignClassifier.load_checkpoint(best_ckpt)
    assert reloaded_model.num_classes == 3
    assert reloaded_model.label_vocab == labels


def test_model_evaluation(tmp_path: Path):
    labels = ["HELLO", "GOODBYE"]
    model = IsolatedSignClassifier(
        model_id="eval_model",
        num_classes=2,
        label_vocab=labels,
        input_dim=24,
        sequence_length=10,
        hidden_dim=16,
        num_layers=1
    )

    test_samples = [
        NormalizedSample(sample_id=f"test_{i}", video_path=f"test_{i}.mp4", task="isolated_sign", label=labels[i % 2], split="test")
        for i in range(8)
    ]

    report = ModelEvaluator.evaluate_isolated(model, test_samples, dataset_name="TestSet")
    assert report.test_sample_count == 8
    assert "accuracy" in report.metrics
    assert report.latency_ms_per_sample >= 0.0

    report_path = tmp_path / "eval_report.json"
    report.save(report_path)
    assert report_path.exists()
