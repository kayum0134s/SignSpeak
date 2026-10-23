"""
Base Dataset Adapter Contract and Manifest Specifications.

Defines the core abstractions, standardized sample representations,
dataset validation protocols, and versioned manifest structures for all
sign language datasets supported by SignSpeak.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator


class TaskType(str, Enum):
    """Supported machine learning training and inference tasks."""
    ISOLATED_SIGN = "isolated_sign"             # Task A: Single sign classification
    CONTINUOUS_GLOSS = "continuous_gloss"       # Task B: Sequence of gloss tokens
    SENTENCE_TRANSLATION = "sentence_translation"# Task C: Sequence-to-English translation


class AnnotationType(str, Enum):
    """Underlying dataset annotation schema."""
    ISOLATED_WORD = "isolated_word"
    GLOSS_SEQUENCE = "gloss_sequence"
    ENGLISH_SENTENCE = "english_sentence"
    MULTIMODAL = "multimodal"


class SplitType(str, Enum):
    """Standard split partitions."""
    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class NormalizedSample(BaseModel):
    """
    Standardized, task-agnostic representation of an individual sign language sample.
    Never fabricates missing labels, timestamps, or signer IDs (defaults to None).
    """
    sample_id: str = Field(..., description="Unique sample identifier within dataset")
    video_path: str = Field(..., description="Path to source video file (relative or absolute)")
    task: str = Field(..., description="Target task type (isolated_sign, continuous_gloss, sentence_translation)")
    sign_language: str = Field("ASL", description="Sign language dialect, e.g. ASL, ISL")
    start_time: Optional[float] = Field(None, description="Start timestamp in seconds if clipped")
    end_time: Optional[float] = Field(None, description="End timestamp in seconds if clipped")
    label: Optional[str] = Field(None, description="Isolated sign label/class (Task A)")
    gloss_sequence: Optional[List[str]] = Field(None, description="Sequential gloss tokens (Task B)")
    english_translation: Optional[str] = Field(None, description="Ground truth English sentence (Task C)")
    signer_id: Optional[str] = Field(None, description="Signer identifier for leakage prevention")
    split: str = Field("train", description="Split partition: train, val, or test")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Adapter-specific metadata")

    @field_validator("split")
    @classmethod
    def validate_split(cls, v: str) -> str:
        clean = v.lower().strip()
        if clean in ("train", "training"):
            return "train"
        if clean in ("val", "validation", "dev"):
            return "val"
        if clean in ("test", "testing", "eval"):
            return "test"
        return clean


class ValidationReport(BaseModel):
    """Comprehensive health, compatibility, and leakage report for a dataset."""
    dataset_name: str
    dataset_version: str
    is_valid: bool
    total_found: int
    valid_count: int
    invalid_count: int
    missing_files_count: int
    split_counts: Dict[str, int] = Field(default_factory=dict)
    signer_ids: List[str] = Field(default_factory=list)
    signer_leakage_detected: bool = False
    signer_leakage_details: Optional[str] = None
    compatible_tasks: List[str] = Field(default_factory=list)
    license_notes: str = ""
    attribution: str = ""
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class DatasetManifest(BaseModel):
    """Versioned internal manifest specification serialized to data/manifests/."""
    manifest_version: str = "1.0.0"
    dataset_name: str
    dataset_version: str
    sign_language: str
    task: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    splits: Dict[str, int] = Field(default_factory=dict)
    total_samples: int
    label_vocab: List[str] = Field(default_factory=list)
    license_info: str = ""
    attribution: str = ""
    samples: List[NormalizedSample]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def save_to_file(self, file_path: Path) -> None:
        """Serializes manifest to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, file_path: Path) -> "DatasetManifest":
        """Loads manifest from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)


class DatasetAdapter(ABC):
    """
    Abstract contract for all SignSpeak dataset adapters.
    Guarantees standard discovery, validation, statistics, and manifest creation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical name of dataset, e.g. 'How2Sign', 'WLASL', 'MS-ASL', 'Custom'."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Dataset version identifier."""
        pass

    @property
    @abstractmethod
    def source(self) -> str:
        """Official source URL or citation."""
        pass

    @property
    @abstractmethod
    def license_info(self) -> str:
        """License name and key restrictions (e.g. Non-Commercial, Academic)."""
        pass

    @property
    @abstractmethod
    def attribution(self) -> str:
        """Required attribution text."""
        pass

    @property
    @abstractmethod
    def annotation_type(self) -> AnnotationType:
        """Primary annotation format."""
        pass

    @property
    @abstractmethod
    def modalities(self) -> List[str]:
        """Available data modalities, e.g. ['video', 'gloss', 'text']."""
        pass

    @property
    @abstractmethod
    def supported_tasks(self) -> List[TaskType]:
        """ML tasks this dataset is fundamentally compatible with."""
        pass

    @property
    def sign_language(self) -> str:
        """Sign language dialect. Defaults to ASL."""
        return "ASL"

    @abstractmethod
    def discover_samples(self, root_dir: Path) -> List[NormalizedSample]:
        """Scans root_dir and parses local raw files into normalized samples."""
        pass

    def check_signer_leakage(self, samples: List[NormalizedSample]) -> tuple[bool, Optional[str]]:
        """
        Detects whether any signer appears in multiple distinct splits (e.g. train and test).
        Signer leakage severely invalidates generalizability evaluation.
        """
        signer_splits: Dict[str, Set[str]] = {}
        for s in samples:
            if s.signer_id:
                signer_splits.setdefault(s.signer_id, set()).add(s.split)

        leaked_signers = {signer: splits for signer, splits in signer_splits.items() if len(splits) > 1}
        if leaked_signers:
            details = ", ".join(f"Signer '{s}' in {sorted(list(splits))}" for s, splits in list(leaked_signers.items())[:5])
            return True, f"Signer leakage detected across splits: {details}"
        return False, None

    def validate(self, root_dir: Path) -> ValidationReport:
        """
        Validates sample existence, format integrity, label coverage,
        signer leakage, and task compatibility.
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        if not root_dir.exists():
            return ValidationReport(
                dataset_name=self.name,
                dataset_version=self.version,
                is_valid=False,
                total_found=0,
                valid_count=0,
                invalid_count=0,
                missing_files_count=0,
                license_notes=self.license_info,
                attribution=self.attribution,
                errors=[f"Dataset directory does not exist: {root_dir}"]
            )

        try:
            samples = self.discover_samples(root_dir)
        except Exception as e:
            return ValidationReport(
                dataset_name=self.name,
                dataset_version=self.version,
                is_valid=False,
                total_found=0,
                valid_count=0,
                invalid_count=0,
                missing_files_count=0,
                license_notes=self.license_info,
                attribution=self.attribution,
                errors=[f"Failed during sample discovery: {str(e)}"]
            )

        total_found = len(samples)
        valid_samples: List[NormalizedSample] = []
        missing_files = 0
        split_counts: Dict[str, int] = {"train": 0, "val": 0, "test": 0}
        signers: Set[str] = set()

        for s in samples:
            # Check video file existence if relative or absolute
            video_file = Path(s.video_path)
            if not video_file.is_absolute():
                video_file = root_dir / video_file

            if not video_file.exists():
                missing_files += 1
                continue

            valid_samples.append(s)
            split_counts[s.split] = split_counts.get(s.split, 0) + 1
            if s.signer_id:
                signers.add(s.signer_id)

        # Check signer leakage
        leakage_detected, leakage_msg = self.check_signer_leakage(valid_samples)
        if leakage_detected:
            warnings.append(leakage_msg or "Signer leakage detected across splits.")

        if total_found == 0:
            errors.append("No samples discovered in dataset directory.")
        elif len(valid_samples) == 0:
            errors.append(f"Discovered {total_found} entries, but all referenced video files are missing on disk.")
        elif missing_files > 0:
            warnings.append(f"{missing_files} of {total_found} samples have missing video files.")

        compatible_tasks = [t.value for t in self.supported_tasks]

        return ValidationReport(
            dataset_name=self.name,
            dataset_version=self.version,
            is_valid=(len(errors) == 0 and len(valid_samples) > 0),
            total_found=total_found,
            valid_count=len(valid_samples),
            invalid_count=missing_files,
            missing_files_count=missing_files,
            split_counts=split_counts,
            signer_ids=sorted(list(signers)),
            signer_leakage_detected=leakage_detected,
            signer_leakage_details=leakage_msg,
            compatible_tasks=compatible_tasks,
            license_notes=self.license_info,
            attribution=self.attribution,
            errors=errors,
            warnings=warnings
        )

    def generate_manifest(
        self,
        root_dir: Path,
        output_path: Optional[Path] = None,
        task: Optional[TaskType] = None
    ) -> DatasetManifest:
        """
        Builds a versioned manifest from valid discovered samples.
        """
        samples = self.discover_samples(root_dir)
        valid_samples: List[NormalizedSample] = []
        vocab_set: Set[str] = set()
        splits: Dict[str, int] = {}

        selected_task = task.value if task else (self.supported_tasks[0].value if self.supported_tasks else "isolated_sign")

        for s in samples:
            # Check video existence
            video_file = Path(s.video_path)
            if not video_file.is_absolute():
                video_file = root_dir / video_file
            if not video_file.exists():
                continue

            # Update sample task if explicitly targeted
            s.task = selected_task
            valid_samples.append(s)
            splits[s.split] = splits.get(s.split, 0) + 1

            if s.label:
                vocab_set.add(s.label.strip().upper())
            if s.gloss_sequence:
                for g in s.gloss_sequence:
                    vocab_set.add(g.strip().upper())

        manifest = DatasetManifest(
            dataset_name=self.name,
            dataset_version=self.version,
            sign_language=self.sign_language,
            task=selected_task,
            splits=splits,
            total_samples=len(valid_samples),
            label_vocab=sorted(list(vocab_set)),
            license_info=self.license_info,
            attribution=self.attribution,
            samples=valid_samples
        )

        if output_path:
            manifest.save_to_file(output_path)

        return manifest
