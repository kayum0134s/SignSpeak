"""
Tests for Dataset Adapters, Manifest Schema, and Validation Protocols.
"""

import json
from pathlib import Path
import pytest
from ml.datasets import (
    CustomDatasetAdapter,
    DatasetManifest,
    How2SignAdapter,
    MSASLAdapter,
    NormalizedSample,
    TaskType,
    WLASLAdapter,
    get_adapter,
    list_adapters,
)


def test_list_and_get_adapters():
    adapters = list_adapters()
    assert "how2sign" in adapters
    assert "wlasl" in adapters
    assert "ms-asl" in adapters
    assert "custom" in adapters

    h2s = get_adapter("how2sign")
    assert isinstance(h2s, How2SignAdapter)

    wlasl = get_adapter("wlasl")
    assert isinstance(wlasl, WLASLAdapter)

    with pytest.raises(ValueError):
        get_adapter("unknown_dataset_xyz")


def test_normalized_sample_schema():
    sample = NormalizedSample(
        sample_id="test_001",
        video_path="videos/test.mp4",
        task="isolated_sign",
        sign_language="ASL",
        label="HELLO",
        signer_id="signer_42",
        split="TRAINING"  # should auto-normalize to train
    )
    assert sample.split == "train"
    assert sample.label == "HELLO"
    assert sample.start_time is None
    assert sample.gloss_sequence is None


def test_manifest_serialization(tmp_path: Path):
    sample = NormalizedSample(
        sample_id="test_001",
        video_path="videos/test.mp4",
        task="isolated_sign",
        sign_language="ASL",
        label="HELLO",
        split="train"
    )
    manifest = DatasetManifest(
        dataset_name="TestDataset",
        dataset_version="1.0",
        sign_language="ASL",
        task="isolated_sign",
        splits={"train": 1},
        total_samples=1,
        label_vocab=["HELLO"],
        samples=[sample]
    )

    out_file = tmp_path / "test_manifest.json"
    manifest.save_to_file(out_file)
    assert out_file.exists()

    loaded = DatasetManifest.load_from_file(out_file)
    assert loaded.dataset_name == "TestDataset"
    assert len(loaded.samples) == 1
    assert loaded.samples[0].label == "HELLO"


def test_custom_adapter_directory_layout(tmp_path: Path):
    # Setup mock class folders with dummy video files
    hello_dir = tmp_path / "hello"
    hello_dir.mkdir()
    (hello_dir / "vid1.mp4").write_text("dummy video")
    (hello_dir / "vid2.mp4").write_text("dummy video")

    thanks_dir = tmp_path / "thank_you"
    thanks_dir.mkdir()
    (thanks_dir / "vid3.mp4").write_text("dummy video")

    adapter = CustomDatasetAdapter()
    samples = adapter.discover_samples(tmp_path)
    assert len(samples) == 3

    labels = {s.label for s in samples}
    assert "hello" in labels
    assert "thank_you" in labels

    # Validation report
    report = adapter.validate(tmp_path)
    assert report.is_valid is True
    assert report.total_found == 3
    assert report.valid_count == 3
    assert report.missing_files_count == 0


def test_custom_adapter_metadata_json(tmp_path: Path):
    (tmp_path / "clip.mp4").write_text("dummy video")
    metadata = [
        {
            "sample_id": "cust_1",
            "video_path": "clip.mp4",
            "task": "sentence_translation",
            "english_translation": "How are you doing today?",
            "gloss_sequence": ["HOW", "YOU", "DOING"],
            "signer_id": "signer_1",
            "split": "train"
        }
    ]
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))

    adapter = CustomDatasetAdapter()
    samples = adapter.discover_samples(tmp_path)
    assert len(samples) == 1
    assert samples[0].english_translation == "How are you doing today?"
    assert samples[0].gloss_sequence == ["HOW", "YOU", "DOING"]
    assert samples[0].signer_id == "signer_1"


def test_signer_leakage_detection(tmp_path: Path):
    (tmp_path / "v1.mp4").write_text("dummy")
    (tmp_path / "v2.mp4").write_text("dummy")

    metadata = [
        {"sample_id": "s1", "video_path": "v1.mp4", "signer_id": "signer_A", "split": "train", "label": "YES"},
        {"sample_id": "s2", "video_path": "v2.mp4", "signer_id": "signer_A", "split": "test", "label": "NO"}
    ]
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))

    adapter = CustomDatasetAdapter()
    report = adapter.validate(tmp_path)
    assert report.signer_leakage_detected is True
    assert "Signer 'signer_A' in ['test', 'train']" in report.signer_leakage_details


def test_wlasl_adapter_parsing(tmp_path: Path):
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    (videos_dir / "12345.mp4").write_text("dummy")

    wlasl_data = [
        {
            "gloss": "book",
            "instances": [
                {
                    "video_id": "12345",
                    "signer_id": 5,
                    "split": "train",
                    "frame_start": 1,
                    "frame_end": 50,
                    "fps": 25.0
                }
            ]
        }
    ]
    (tmp_path / "WLASL_v0.3.json").write_text(json.dumps(wlasl_data))

    adapter = WLASLAdapter()
    assert adapter.annotation_type.value == "isolated_word"
    assert TaskType.ISOLATED_SIGN in adapter.supported_tasks

    samples = adapter.discover_samples(tmp_path)
    assert len(samples) == 1
    assert samples[0].label == "BOOK"
    assert samples[0].start_time == 0.04
    assert samples[0].end_time == 2.0
    assert samples[0].split == "train"

    report = adapter.validate(tmp_path)
    assert report.is_valid is True
    assert report.valid_count == 1


def test_how2sign_adapter_parsing(tmp_path: Path):
    (tmp_path / "sentence_01.mp4").write_text("dummy")
    csv_content = "SENTENCE_NAME,START_REALIGNED,END_REALIGNED,SENTENCE,GLOSS\nsentence_01,0.5,3.2,Hello everyone,HELLO EVERYONE\n"
    (tmp_path / "how2sign_realigned_train.csv").write_text(csv_content)

    adapter = How2SignAdapter()
    assert TaskType.SENTENCE_TRANSLATION in adapter.supported_tasks
    assert TaskType.CONTINUOUS_GLOSS in adapter.supported_tasks

    samples = adapter.discover_samples(tmp_path)
    assert len(samples) == 1
    assert samples[0].english_translation == "Hello everyone"
    assert samples[0].gloss_sequence == ["HELLO", "EVERYONE"]
    assert samples[0].split == "train"

    manifest = adapter.generate_manifest(tmp_path)
    assert manifest.total_samples == 1
    assert "HELLO" in manifest.label_vocab
    assert "EVERYONE" in manifest.label_vocab
