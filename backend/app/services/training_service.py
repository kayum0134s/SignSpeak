"""
Background Training Job Service.
Executes model training jobs asynchronously in background threads,
protecting CPU and memory resources by enforcing a single-job concurrency limit.
Streams real-time progress and automatically registers verified checkpoints.
"""

from datetime import datetime, timezone
from pathlib import Path
import threading
import time
import traceback
from typing import Any, Dict, List, Optional
import torch

from ml.datasets import get_adapter
from ml.datasets.base import DatasetManifest, TaskType
from ml.models.continuous_seq2seq import ContinuousGlossRecognizer
from ml.models.isolated_classifier import IsolatedSignClassifier
from ml.models.translation_pipeline import (
    GlossToEnglishTranslator,
    SignTranslationPipeline,
)
from ml.preprocessing.vocabulary import Vocabulary
from ml.registry.registry import (
    LocalModelRegistry,
    RegisteredModelInfo,
)
from ml.training.config import TrainingConfig
from ml.training.trainer import (
    ContinuousGlossDataset,
    ContinuousGlossTrainer,
    IsolatedSignDataset,
    IsolatedSignTrainer,
)


class TrainingJobStatus:
    def __init__(self, job_id: str, config: TrainingConfig):
        self.job_id = job_id
        self.config = config
        self.state: str = "running"  # running, completed, failed, cancelled
        self.current_epoch: int = 0
        self.total_epochs: int = config.epochs
        self.train_loss: float = 0.0
        self.val_loss: float = 0.0
        self.val_acc: float = 0.0
        self.is_best: bool = False
        self.logs: List[str] = []
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None

    def add_log(self, message: str):
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        duration = (self.end_time or time.time()) - self.start_time
        return {
            "job_id": self.job_id,
            "state": self.state,
            "task": self.config.task,
            "model_id": self.config.model_id,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "train_loss": round(self.train_loss, 4),
            "val_loss": round(self.val_loss, 4),
            "val_acc": round(self.val_acc, 4),
            "is_best": self.is_best,
            "duration_seconds": round(duration, 1),
            "error_message": self.error_message,
            "logs": self.logs[-50:],  # return last 50 log lines
            "result": self.result
        }


class TrainingService:
    """Manages background ML training execution."""

    def __init__(self, registry: Optional[LocalModelRegistry] = None):
        self.registry = registry or LocalModelRegistry()
        self.active_job: Optional[TrainingJobStatus] = None
        self.active_trainer: Optional[Any] = None
        self._lock = threading.Lock()

    def start_training_job(self, config: TrainingConfig) -> TrainingJobStatus:
        with self._lock:
            if self.active_job and self.active_job.state == "running":
                raise RuntimeError("A training job is already currently in progress. Concurrency limit is 1.")

            job_id = f"job_{config.model_id}_{int(time.time())}"
            job_status = TrainingJobStatus(job_id=job_id, config=config)
            self.active_job = job_status

            # Spawn worker thread
            thread = threading.Thread(
                target=self._run_training_worker,
                args=(job_status,),
                daemon=True
            )
            thread.start()
            return job_status

    def cancel_training_job(self) -> Dict[str, Any]:
        with self._lock:
            if not self.active_job or self.active_job.state != "running":
                return {"message": "No active training job to cancel."}

            if self.active_trainer:
                self.active_trainer.cancel()
            self.active_job.state = "cancelled"
            self.active_job.add_log("Training cancellation requested by user.")
            return {"message": "Training cancellation requested."}

    def get_current_job_status(self) -> Dict[str, Any]:
        if not self.active_job:
            return {"state": "idle", "message": "No training job has been executed yet."}
        return self.active_job.to_dict()

    def _run_training_worker(self, job: TrainingJobStatus):
        config = job.config
        job.add_log(f"Starting training job for task '{config.task}' on model '{config.model_id}'")
        job.add_log(f"Execution device: {config.device}, Batch size: {config.batch_size}, Max epochs: {config.epochs}")

        try:
            # 1. Load Manifest
            manifest_file = Path(config.manifest_path)
            if not manifest_file.exists():
                raise FileNotFoundError(f"Manifest not found at {manifest_file}")

            manifest = DatasetManifest.load_from_file(manifest_file)
            job.add_log(f"Loaded manifest '{manifest.dataset_name}' with {manifest.total_samples} samples.")

            train_samples = [s for s in manifest.samples if s.split == "train"]
            val_samples = [s for s in manifest.samples if s.split == "val"]
            if not val_samples:
                # If no val split, use 20% of train
                val_samples = train_samples[-max(1, len(train_samples) // 5):]
                train_samples = train_samples[:-len(val_samples)]

            job.add_log(f"Train samples: {len(train_samples)}, Val samples: {len(val_samples)}")

            # 2. Setup Task Specific Model & Datasets
            if config.task == TaskType.ISOLATED_SIGN.value:
                vocab_list = manifest.label_vocab or sorted(list({s.label for s in manifest.samples if s.label}))
                if not vocab_list:
                    vocab_list = ["UNKNOWN_SIGN"]
                vocab = Vocabulary(vocab_list)

                train_ds = IsolatedSignDataset(train_samples, vocab, sequence_length=config.sequence_length, input_dim=config.input_dim)
                val_ds = IsolatedSignDataset(val_samples, vocab, sequence_length=config.sequence_length, input_dim=config.input_dim)

                model = IsolatedSignClassifier(
                    model_id=config.model_id,
                    num_classes=len(vocab),
                    label_vocab=vocab_list,
                    input_dim=config.input_dim,
                    sequence_length=config.sequence_length,
                    hidden_dim=config.hidden_dim,
                    num_layers=config.num_layers,
                    dropout=config.dropout
                )
                trainer = IsolatedSignTrainer(config, model, train_ds, val_ds)

            elif config.task == TaskType.CONTINUOUS_GLOSS.value:
                vocab_list = manifest.label_vocab
                if not vocab_list:
                    all_glosses = set()
                    for s in manifest.samples:
                        if s.gloss_sequence:
                            all_glosses.update(s.gloss_sequence)
                    vocab_list = sorted(list(all_glosses)) or ["HELLO", "WORLD"]

                vocab = Vocabulary(vocab_list, ctc_mode=True)
                train_ds = ContinuousGlossDataset(train_samples, vocab, sequence_length=config.sequence_length, input_dim=config.input_dim)
                val_ds = ContinuousGlossDataset(val_samples, vocab, sequence_length=config.sequence_length, input_dim=config.input_dim)

                model = ContinuousGlossRecognizer(
                    model_id=config.model_id,
                    gloss_vocab=vocab_list,
                    input_dim=config.input_dim,
                    hidden_dim=config.hidden_dim,
                    num_layers=config.num_layers,
                    dropout=config.dropout
                )
                trainer = ContinuousGlossTrainer(config, model, train_ds, val_ds)

            elif config.task == TaskType.SENTENCE_TRANSLATION.value:
                vocab_list = manifest.label_vocab or ["HELLO", "THANK_YOU"]
                vocab = Vocabulary(vocab_list, ctc_mode=True)
                train_ds = ContinuousGlossDataset(train_samples, vocab, sequence_length=config.sequence_length, input_dim=config.input_dim)
                val_ds = ContinuousGlossDataset(val_samples, vocab, sequence_length=config.sequence_length, input_dim=config.input_dim)

                recognizer = ContinuousGlossRecognizer(
                    model_id=f"{config.model_id}_rec",
                    gloss_vocab=vocab_list,
                    input_dim=config.input_dim,
                    hidden_dim=config.hidden_dim,
                    num_layers=config.num_layers,
                    dropout=config.dropout
                )
                trainer = ContinuousGlossTrainer(config, recognizer, train_ds, val_ds)

            self.active_trainer = trainer

            # Progress callback
            def progress_hook(info: Dict[str, Any]):
                job.current_epoch = info["epoch"]
                job.train_loss = info.get("train_loss", 0.0)
                job.val_loss = info.get("val_loss", 0.0)
                job.val_acc = info.get("val_acc", 0.0)
                job.is_best = info.get("is_best", False)
                best_star = " ⭐ (New Best)" if job.is_best else ""
                job.add_log(f"Epoch {job.current_epoch}/{job.total_epochs} - Loss: {job.train_loss:.4f}, Val Loss: {job.val_loss:.4f}, Val Acc: {job.val_acc:.4f}{best_star}")

            result = trainer.train(progress_callback=progress_hook)
            job.result = result
            job.end_time = time.time()

            if result["status"] == "completed":
                job.state = "completed"
                ckpt_path = Path(result["checkpoint_path"])
                job.add_log(f"Training completed successfully! Saved checkpoint to {ckpt_path}")

                # Register the newly trained model in the registry!
                sha = LocalModelRegistry.calculate_sha256(ckpt_path)
                reg_info = RegisteredModelInfo(
                    model_id=config.model_id,
                    version="1.0.0",
                    task=config.task,
                    sign_language=manifest.sign_language,
                    dataset_sources=[manifest.dataset_name],
                    vocabulary=vocab_list,
                    num_classes=len(vocab_list),
                    preprocessing={"input_dim": config.input_dim, "sequence_length": config.sequence_length},
                    architecture=config.model_architecture,
                    checkpoint_path=str(ckpt_path),
                    checksum_sha256=sha,
                    training_config=config.model_dump(),
                    evaluation_metrics={"val_loss": result.get("best_val_loss"), "val_acc": result.get("best_val_acc")},
                    license_info=manifest.license_info,
                    attribution=manifest.attribution,
                    known_limitations=[f"Trained on {manifest.dataset_name} ({len(train_samples)} training samples)"]
                )
                self.registry.register_model(reg_info)
                job.add_log(f"Registered model '{config.model_id}' in Model Registry.")
            else:
                job.state = "cancelled"
                job.add_log("Training was cancelled.")

        except Exception as e:
            job.state = "failed"
            job.end_time = time.time()
            job.error_message = str(e)
            job.add_log(f"Training error: {str(e)}")
            job.add_log(traceback.format_exc())
        finally:
            self.active_trainer = None


# Global singleton training service
training_service = TrainingService()
