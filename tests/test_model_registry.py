"""
Tests for Phase 6: Model Registry, Checkpoint Verification, and Task Compatibility.
"""

from pathlib import Path
import pytest
import torch

from ml.datasets.base import TaskType
from ml.models.isolated_classifier import IsolatedSignClassifier
from ml.registry.registry import (
    CheckpointVerificationError,
    IncompatibleTaskError,
    LocalModelRegistry,
    RegisteredModelInfo,
)


def test_registry_registration_and_retrieval(tmp_path: Path):
    registry = LocalModelRegistry(registry_dir=tmp_path / "registry")

    # Create dummy checkpoint
    labels = ["HELLO", "GOODBYE"]
    model = IsolatedSignClassifier(
        model_id="reg_test_model",
        num_classes=2,
        label_vocab=labels,
        input_dim=24,
        sequence_length=10,
        hidden_dim=16,
        num_layers=1
    )
    ckpt_file = tmp_path / "test_ckpt.pt"
    model.save_checkpoint(ckpt_file)

    sha = LocalModelRegistry.calculate_sha256(ckpt_file)
    info = RegisteredModelInfo(
        model_id="reg_test_model",
        version="1.0.0",
        task="isolated_sign",
        vocabulary=labels,
        num_classes=2,
        architecture="BiGRU_Attention_Classifier",
        checkpoint_path=str(ckpt_file),
        checksum_sha256=sha
    )

    registered = registry.register_model(info)
    assert registered.model_id == "reg_test_model"

    # Retrieve
    retrieved = registry.get_model_info("reg_test_model")
    assert retrieved is not None
    assert retrieved.num_classes == 2
    assert retrieved.task == "isolated_sign"

    # List
    all_models = registry.list_models()
    assert len(all_models) == 1
    assert all_models[0].model_id == "reg_test_model"


def test_checksum_verification_and_corruption_detection(tmp_path: Path):
    registry = LocalModelRegistry(registry_dir=tmp_path / "registry")
    ckpt_file = tmp_path / "model.pt"
    ckpt_file.write_text("valid checkpoint data")

    sha = LocalModelRegistry.calculate_sha256(ckpt_file)
    info = RegisteredModelInfo(
        model_id="corrupt_check_model",
        version="1.0.0",
        task="isolated_sign",
        vocabulary=["A", "B"],
        num_classes=2,
        architecture="BiGRU",
        checkpoint_path=str(ckpt_file),
        checksum_sha256=sha
    )
    registry.register_model(info)

    # Now corrupt the checkpoint file
    ckpt_file.write_text("tampered corrupted data")

    with pytest.raises(CheckpointVerificationError):
        registry.load_model_instance("corrupt_check_model")


def test_task_compatibility_enforcement(tmp_path: Path):
    registry = LocalModelRegistry(registry_dir=tmp_path / "registry")
    ckpt_file = tmp_path / "dummy.pt"
    ckpt_file.write_text("data")

    sha = LocalModelRegistry.calculate_sha256(ckpt_file)
    info = RegisteredModelInfo(
        model_id="isolated_only_model",
        version="1.0.0",
        task="isolated_sign",
        vocabulary=["HELLO"],
        num_classes=1,
        architecture="BiGRU",
        checkpoint_path=str(ckpt_file),
        checksum_sha256=sha
    )
    registry.register_model(info, verify_checkpoint=False)

    # Isolated task should succeed
    compat = registry.assert_task_compatibility("isolated_only_model", TaskType.ISOLATED_SIGN)
    assert compat.model_id == "isolated_only_model"

    # Continuous or Translation task must raise IncompatibleTaskError
    with pytest.raises(IncompatibleTaskError):
        registry.assert_task_compatibility("isolated_only_model", TaskType.SENTENCE_TRANSLATION)

    with pytest.raises(IncompatibleTaskError):
        registry.assert_task_compatibility("isolated_only_model", TaskType.CONTINUOUS_GLOSS)


def test_active_model_selection(tmp_path: Path):
    registry = LocalModelRegistry(registry_dir=tmp_path / "registry")
    ckpt = tmp_path / "test.pt"
    ckpt.write_text("dummy")

    sha = LocalModelRegistry.calculate_sha256(ckpt)
    info1 = RegisteredModelInfo(
        model_id="model_v1",
        version="1.0.0",
        task="isolated_sign",
        vocabulary=["YES"],
        num_classes=1,
        architecture="BiGRU",
        checkpoint_path=str(ckpt),
        checksum_sha256=sha
    )
    info2 = RegisteredModelInfo(
        model_id="model_v2",
        version="2.0.0",
        task="isolated_sign",
        vocabulary=["YES", "NO"],
        num_classes=2,
        architecture="BiGRU",
        checkpoint_path=str(ckpt),
        checksum_sha256=sha
    )

    registry.register_model(info1, verify_checkpoint=False)
    registry.register_model(info2, verify_checkpoint=False)

    registry.set_active_model("model_v2", TaskType.ISOLATED_SIGN)
    active = registry.get_active_model(TaskType.ISOLATED_SIGN)
    assert active is not None
    assert active.model_id == "model_v2"
