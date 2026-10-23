"""
How2Sign Dataset Adapter.
Supports How2Sign multimodal continuous sign language dataset:
- Continuous ASL video recordings
- Aligned English translations
- Sequential ASL gloss annotations
- Signer-independent official train/val/test splits
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
from ml.datasets.base import (
    AnnotationType,
    DatasetAdapter,
    NormalizedSample,
    TaskType,
)


class How2SignAdapter(DatasetAdapter):
    """
    Adapter for How2Sign continuous American Sign Language dataset.
    Reference: Duarte et al., 'How2Sign: A Large-Scale Multimodal Dataset for Continuous American Sign Language' (CVPR 2021).
    """

    @property
    def name(self) -> str:
        return "How2Sign"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def source(self) -> str:
        return "https://how2sign.github.io/"

    @property
    def license_info(self) -> str:
        return "CC BY-NC-SA 4.0 (Non-Commercial, Academic Use Only)"

    @property
    def attribution(self) -> str:
        return "Duarte et al., CVPR 2021 - How2Sign dataset"

    @property
    def annotation_type(self) -> AnnotationType:
        return AnnotationType.MULTIMODAL

    @property
    def modalities(self) -> List[str]:
        return ["video", "landmarks", "gloss", "text"]

    @property
    def supported_tasks(self) -> List[TaskType]:
        return [
            TaskType.CONTINUOUS_GLOSS,
            TaskType.SENTENCE_TRANSLATION
        ]

    def _parse_csv(self, csv_file: Path, split_name: str, video_dir: Path, root_dir: Path) -> List[NormalizedSample]:
        samples: List[NormalizedSample] = []
        if not csv_file.exists():
            return samples

        with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
            # Check delimiter (comma or tab)
            sample_line = f.readline()
            delimiter = "\t" if "\t" in sample_line else ","
            f.seek(0)
            reader = csv.DictReader(f, delimiter=delimiter)

            for idx, row in enumerate(reader):
                # Standard How2Sign column headers:
                # SENTENCE_NAME, START_REALIGNED, END_REALIGNED, SENTENCE, or SENTENCE_NAME, START, END, TEXT
                sentence_id = (
                    row.get("SENTENCE_NAME") or
                    row.get("sentence_name") or
                    row.get("NAME") or
                    f"{split_name}_{idx:05d}"
                )
                start_val = row.get("START_REALIGNED") or row.get("START") or row.get("start")
                end_val = row.get("END_REALIGNED") or row.get("END") or row.get("end")
                sentence = (
                    row.get("SENTENCE") or
                    row.get("sentence") or
                    row.get("TEXT") or
                    row.get("text") or
                    ""
                ).strip()
                gloss_text = row.get("GLOSS") or row.get("gloss")
                glosses = [g.strip().upper() for g in gloss_text.split()] if gloss_text else None
                signer_id = row.get("SIGNER_ID") or row.get("signer_id") or row.get("SPEAKER_ID")

                # Derive signer from sentence_id if standard How2Sign naming e.g. "raw_signer01_..."
                if not signer_id and "signer" in sentence_id.lower():
                    import re
                    match = re.search(r"signer(\d+)", sentence_id.lower())
                    if match:
                        signer_id = f"signer_{match.group(1)}"

                # Match video file
                video_filename = f"{sentence_id}.mp4"
                if video_dir.resolve() == root_dir.resolve():
                    rel_video_path = video_filename
                else:
                    rel_video_path = f"{video_dir.name}/{video_filename}"

                sample = NormalizedSample(
                    sample_id=sentence_id,
                    video_path=str(rel_video_path).replace("\\", "/"),
                    task=TaskType.SENTENCE_TRANSLATION.value,
                    sign_language="ASL",
                    start_time=float(start_val) if start_val is not None and start_val != "" else None,
                    end_time=float(end_val) if end_val is not None and end_val != "" else None,
                    label=None,
                    gloss_sequence=glosses,
                    english_translation=sentence if sentence else None,
                    signer_id=signer_id,
                    split=split_name,
                    metadata={"how2sign_id": sentence_id}
                )
                samples.append(sample)

        return samples

    def discover_samples(self, root_dir: Path) -> List[NormalizedSample]:
        root = Path(root_dir)
        samples: List[NormalizedSample] = []

        # Look for standard split CSV files:
        # how2sign_realigned_train.csv, how2sign_realigned_val.csv, how2sign_realigned_test.csv
        for split_key in ["train", "val", "test"]:
            # Find candidate csv files
            candidates = list(root.glob(f"*{split_key}*.csv")) + list(root.glob(f"*{split_key}*.tsv"))
            video_dir = root / f"{split_key}_videos"
            if not video_dir.exists():
                video_dir = root / "videos"
            if not video_dir.exists():
                video_dir = root

            for csv_f in candidates:
                split_samples = self._parse_csv(csv_f, split_key, video_dir, root)
                samples.extend(split_samples)

        # Fallback if no CSV splits found: look for a single metadata.csv or all mp4 files
        if not samples:
            all_csvs = list(root.glob("*.csv"))
            for csv_f in all_csvs:
                samples.extend(self._parse_csv(csv_f, "train", root, root))

        return samples
