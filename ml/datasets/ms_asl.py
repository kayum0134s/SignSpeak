"""
MS-ASL (Microsoft American Sign Language) Dataset Adapter.
Supports isolated word ASL clips:
- 1,000 sign vocabulary
- Official MSASL_train.json, MSASL_val.json, MSASL_test.json
- Bounding boxes, timestamps, and signer IDs
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from ml.datasets.base import (
    AnnotationType,
    DatasetAdapter,
    NormalizedSample,
    TaskType,
)


class MSASLAdapter(DatasetAdapter):
    """
    Adapter for Microsoft ASL dataset.
    Reference: Vaezi Joze et al., 'MS-ASL: A Large-Scale Data Set and Benchmark for Understanding American Sign Language' (BMVC 2019).
    """

    @property
    def name(self) -> str:
        return "MS-ASL"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def source(self) -> str:
        return "https://www.microsoft.com/en-us/research/project/ms-asl/"

    @property
    def license_info(self) -> str:
        return "Microsoft Research Open Data License / Academic Evaluation Only"

    @property
    def attribution(self) -> str:
        return "Vaezi Joze et al., BMVC 2019 - MS-ASL Dataset"

    @property
    def annotation_type(self) -> AnnotationType:
        return AnnotationType.ISOLATED_WORD

    @property
    def modalities(self) -> List[str]:
        return ["video", "landmarks", "gloss"]

    @property
    def supported_tasks(self) -> List[TaskType]:
        return [TaskType.ISOLATED_SIGN]

    def _parse_split_json(self, json_file: Path, split_name: str, video_dir: Path) -> List[NormalizedSample]:
        samples: List[NormalizedSample] = []
        if not json_file.exists():
            return samples

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return samples

        for idx, entry in enumerate(data):
            clean_text = (entry.get("clean_text") or entry.get("org_text") or "").strip().upper()
            start_time = entry.get("start_time")
            end_time = entry.get("end_time")
            signer_id = str(entry.get("signer_id")) if entry.get("signer_id") is not None else None
            video_id = entry.get("video_id") or f"{split_name}_{idx:05d}"
            
            # MS-ASL files typically named: {video_id}_{start}_{end}.mp4 or {video_id}.mp4
            video_filename = f"{video_id}.mp4"
            rel_path = f"videos/{video_filename}" if video_dir.name == "videos" else video_filename

            sample = NormalizedSample(
                sample_id=f"{video_id}_{idx}",
                video_path=str(rel_path).replace("\\", "/"),
                task=TaskType.ISOLATED_SIGN.value,
                sign_language="ASL",
                start_time=float(start_time) if start_time is not None else None,
                end_time=float(end_time) if end_time is not None else None,
                label=clean_text,
                gloss_sequence=[clean_text] if clean_text else None,
                english_translation=None,
                signer_id=signer_id,
                split=split_name,
                metadata={"box": entry.get("box", [])}
            )
            samples.append(sample)

        return samples

    def discover_samples(self, root_dir: Path) -> List[NormalizedSample]:
        root = Path(root_dir)
        samples: List[NormalizedSample] = []

        video_dir = root / "videos"
        if not video_dir.exists():
            video_dir = root

        for split_key in ["train", "val", "test"]:
            candidates = list(root.glob(f"*{split_key}*.json"))
            for c in candidates:
                samples.extend(self._parse_split_json(c, split_key, video_dir))

        return samples
