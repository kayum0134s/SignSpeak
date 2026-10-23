"""
WLASL (Word-Level American Sign Language) Dataset Adapter.
Supports isolated word ASL clips:
- 2,000 isolated gloss vocabulary
- Subsets: WLASL-100, WLASL-300, WLASL-1000, WLASL-2000
- Official signer IDs and train/val/test splits
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


class WLASLAdapter(DatasetAdapter):
    """
    Adapter for WLASL isolated American Sign Language dataset.
    Reference: Li et al., 'Word-level Deep Sign Language Recognition from Video' (WACV 2020).
    """

    def __init__(self, subset_size: Optional[int] = None):
        self.subset_size = subset_size

    @property
    def name(self) -> str:
        suffix = f"-{self.subset_size}" if self.subset_size else ""
        return f"WLASL{suffix}"

    @property
    def version(self) -> str:
        return "v0.3"

    @property
    def source(self) -> str:
        return "https://dxli94.github.io/WLASL/"

    @property
    def license_info(self) -> str:
        return "Research and Educational Use Only. Videos subject to original web licenses."

    @property
    def attribution(self) -> str:
        return "Dongxu Li et al., WACV 2020 - WLASL Dataset"

    @property
    def annotation_type(self) -> AnnotationType:
        return AnnotationType.ISOLATED_WORD

    @property
    def modalities(self) -> List[str]:
        return ["video", "landmarks", "gloss"]

    @property
    def supported_tasks(self) -> List[TaskType]:
        # WLASL provides isolated words only, NOT sentence grammar
        return [TaskType.ISOLATED_SIGN]

    def discover_samples(self, root_dir: Path) -> List[NormalizedSample]:
        root = Path(root_dir)
        samples: List[NormalizedSample] = []

        # Find WLASL JSON annotations (e.g. WLASL_v0.3.json or nslt_*.json)
        json_candidates = list(root.glob("*WLASL*.json")) + list(root.glob("*.json"))
        if not json_candidates:
            return samples

        # Prefer WLASL_v0.3.json if present
        annotation_file = json_candidates[0]
        for c in json_candidates:
            if "v0.3" in c.name or "wlasl" in c.name.lower():
                annotation_file = c
                break

        video_dir = root / "videos"
        if not video_dir.exists():
            video_dir = root

        with open(annotation_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            # Check if dict with gloss keys or instances
            return samples

        # Process entries
        for gloss_entry in data:
            gloss = gloss_entry.get("gloss", "").strip().upper()
            instances = gloss_entry.get("instances", [])

            for inst in instances:
                video_id = inst.get("video_id") or inst.get("instance_id")
                if not video_id:
                    continue

                split = inst.get("split", "train").lower()
                signer_id = str(inst.get("signer_id")) if inst.get("signer_id") is not None else None
                start_frame = inst.get("frame_start", 1)
                end_frame = inst.get("frame_end", -1)
                fps = inst.get("fps", 25.0)

                start_sec = (start_frame / fps) if start_frame and fps else None
                end_sec = (end_frame / fps) if end_frame and end_frame > 0 and fps else None

                video_filename = f"{video_id}.mp4"
                rel_path = f"videos/{video_filename}" if (root / "videos").exists() else video_filename

                sample = NormalizedSample(
                    sample_id=str(video_id),
                    video_path=str(rel_path).replace("\\", "/"),
                    task=TaskType.ISOLATED_SIGN.value,
                    sign_language="ASL",
                    start_time=start_sec,
                    end_time=end_sec,
                    label=gloss,
                    gloss_sequence=[gloss],
                    english_translation=None,
                    signer_id=signer_id,
                    split=split,
                    metadata={"original_gloss": gloss, "fps": fps}
                )
                samples.append(sample)

        return samples
