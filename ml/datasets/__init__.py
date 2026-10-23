"""
SignSpeak Dataset Adapters and Interfaces.
"""

from typing import Dict, List, Type
from ml.datasets.base import (
    AnnotationType,
    DatasetAdapter,
    DatasetManifest,
    NormalizedSample,
    SplitType,
    TaskType,
    ValidationReport,
)
from ml.datasets.custom import CustomDatasetAdapter
from ml.datasets.how2sign import How2SignAdapter
from ml.datasets.ms_asl import MSASLAdapter
from ml.datasets.wlasl import WLASLAdapter

ADAPTER_REGISTRY: Dict[str, Type[DatasetAdapter]] = {
    "custom": CustomDatasetAdapter,
    "how2sign": How2SignAdapter,
    "wlasl": WLASLAdapter,
    "ms-asl": MSASLAdapter,
    "msasl": MSASLAdapter,
}


def get_adapter(name: str, **kwargs) -> DatasetAdapter:
    """Instantiates a dataset adapter by canonical name."""
    key = name.lower().strip()
    if key not in ADAPTER_REGISTRY:
        raise ValueError(
            f"Unknown dataset adapter '{name}'. Available adapters: {list_adapters()}"
        )
    return ADAPTER_REGISTRY[key](**kwargs)


def list_adapters() -> List[str]:
    """Returns list of registered dataset adapter names."""
    return ["how2sign", "wlasl", "ms-asl", "custom"]


__all__ = [
    "AnnotationType",
    "DatasetAdapter",
    "DatasetManifest",
    "NormalizedSample",
    "SplitType",
    "TaskType",
    "ValidationReport",
    "CustomDatasetAdapter",
    "How2SignAdapter",
    "WLASLAdapter",
    "MSASLAdapter",
    "get_adapter",
    "list_adapters",
]
