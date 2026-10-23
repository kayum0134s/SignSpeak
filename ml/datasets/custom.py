"""
Custom Dataset Adapter.
Supports local directories with class folders, annotations.csv, or metadata.json.
Allows users to easily train on proprietary or custom recorded ASL datasets.
"""

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from ml.datasets.base import (
    AnnotationType,
    DatasetAdapter,
    NormalizedSample,
    TaskType,
)


class CustomDatasetAdapter(DatasetAdapter):
    """Adapter for custom local datasets."""

    def __init__(
        self,
        dataset_name: str = "Custom-ASL",
        version: str = "1.0",
        license_info: str = "User-Provided Local Dataset / Proprietary",
        attribution: str = "Local Custom Sign Data",
        sign_language: str = "ASL"
    ):
        self._name = dataset_name
        self._version = version
        self._license = license_info
        self._attribution = attribution
        self._sign_lang = sign_language

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def source(self) -> str:
        return "Local Filesystem"

    @property
    def license_info(self) -> str:
        return self._license

    @property
    def attribution(self) -> str:
        return self._attribution

    @property
    def annotation_type(self) -> AnnotationType:
        return AnnotationType.MULTIMODAL

    @property
    def modalities(self) -> List[str]:
        return ["video", "landmarks", "text"]

    @property
    def supported_tasks(self) -> List[TaskType]:
        return [
            TaskType.ISOLATED_SIGN,
            TaskType.CONTINUOUS_GLOSS,
            TaskType.SENTENCE_TRANSLATION
        ]

    @property
    def sign_language(self) -> str:
        return self._sign_lang

    def _determine_split(self, sample_id: str, signer_id: Optional[str] = None) -> str:
        """
        Deterministically assigns train (70%), val (15%), or test (15%).
        Uses signer_id if available to avoid signer leakage!
        """
        key = signer_id if signer_id else sample_id
        h = int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16) % 100
        if h < 70:
            return "train"
        elif h < 85:
            return "val"
        else:
            return "test"

    def discover_samples(self, root_dir: Path) -> List[NormalizedSample]:
        root = Path(root_dir)
        samples: List[NormalizedSample] = []

        # 1. Check for metadata.json or annotations.json
        json_meta = root / "metadata.json"
        if not json_meta.exists():
            json_meta = root / "annotations.json"

        if json_meta.exists():
            with open(json_meta, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            items = raw_data if isinstance(raw_data, list) else raw_data.get("samples", [])
            for idx, item in enumerate(items):
                sample_id = str(item.get("sample_id", f"sample_{idx:04d}"))
                vpath = item.get("video_path") or item.get("path") or ""
                # resolve relative path
                signer_id = item.get("signer_id")
                split = item.get("split") or self._determine_split(sample_id, signer_id)
                task = item.get("task", TaskType.ISOLATED_SIGN.value)

                sample = NormalizedSample(
                    sample_id=sample_id,
                    video_path=str(vpath),
                    task=task,
                    sign_language=item.get("sign_language", self.sign_language),
                    start_time=item.get("start_time"),
                    end_time=item.get("end_time"),
                    label=item.get("label"),
                    gloss_sequence=item.get("gloss_sequence"),
                    english_translation=item.get("english_translation"),
                    signer_id=signer_id,
                    split=split,
                    metadata=item.get("metadata", {})
                )
                samples.append(sample)
            return samples

        # 2. Check for annotations.csv
        csv_meta = root / "annotations.csv"
        if csv_meta.exists():
            with open(csv_meta, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    sample_id = row.get("sample_id") or f"sample_{idx:04d}"
                    vpath = row.get("video_path") or row.get("filename") or ""
                    signer_id = row.get("signer_id") or None
                    split = row.get("split") or self._determine_split(sample_id, signer_id)
                    label = row.get("label") or None
                    gloss_str = row.get("gloss_sequence")
                    glosses = [g.strip() for g in gloss_str.split()] if gloss_str else None
                    english = row.get("english_translation") or None
                    task = row.get("task", TaskType.ISOLATED_SIGN.value)

                    sample = NormalizedSample(
                        sample_id=sample_id,
                        video_path=vpath,
                        task=task,
                        sign_language=row.get("sign_language", self.sign_language),
                        label=label,
                        gloss_sequence=glosses,
                        english_translation=english,
                        signer_id=signer_id,
                        split=split
                    )
                    samples.append(sample)
            return samples

        # 3. Directory layout scanning: class subfolders or flat video files
        video_exts = {".mp4", ".avi", ".mov", ".webm", ".mkv"}
        all_videos = [p for p in root.rglob("*") if p.suffix.lower() in video_exts]

        for p in all_videos:
            rel_path = p.relative_to(root)
            # If organized in a subfolder, e.g. root/hello/001.mp4
            if len(rel_path.parts) > 1:
                label = rel_path.parts[0]
            else:
                label = p.stem.replace("_", " ").title()

            sample_id = p.stem
            split = self._determine_split(sample_id)
            sample = NormalizedSample(
                sample_id=sample_id,
                video_path=str(rel_path).replace("\\", "/"),
                task=TaskType.ISOLATED_SIGN.value,
                sign_language=self.sign_language,
                label=label,
                split=split
            )
            samples.append(sample)

        return samples
