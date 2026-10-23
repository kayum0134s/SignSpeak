"""
SignSpeak ML Pipeline Command Line Interface (CLI).
Enables dataset inspection, validation, manifest preparation, model training,
checkpoint evaluation, registry management, and local server startup.
"""

import argparse
import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe UTF-8 console output for Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from ml.datasets import get_adapter, list_adapters
from ml.datasets.base import TaskType
from ml.evaluation.evaluator import ModelEvaluator
from ml.models.base import BaseSignModel
from ml.registry.registry import LocalModelRegistry, RegisteredModelInfo
from ml.training.config import TrainingConfig
from ml.training.trainer import (
    ContinuousGlossDataset,
    ContinuousGlossTrainer,
    IsolatedSignDataset,
    IsolatedSignTrainer,
)


def cmd_inspect(args):
    adapter = get_adapter(args.dataset)
    print("=" * 60)
    print(f"📊 Dataset Adapter: {adapter.name} ({adapter.version})")
    print(f"🔗 Source: {adapter.source}")
    print(f"📜 License: {adapter.license_info}")
    print(f"✍️ Attribution: {adapter.attribution}")
    print(f"🏷️ Annotation Type: {adapter.annotation_type.value}")
    print(f"👁️ Modalities: {', '.join(adapter.modalities)}")
    print(f"🎯 Supported Tasks: {[t.value for t in adapter.supported_tasks]}")
    print("=" * 60)


def cmd_validate(args):
    adapter = get_adapter(args.dataset)
    path = Path(args.path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    print(f"🔍 Validating directory: {path} against {adapter.name} adapter...")
    report = adapter.validate(path)

    print("\n" + "=" * 60)
    print(f"Result: {'✓ VALID' if report.is_valid else '✕ INVALID'}")
    print(f"Total Discovered: {report.total_found}")
    print(f"Valid Samples:    {report.valid_count}")
    print(f"Missing Files:    {report.missing_files_count}")
    print(f"Splits Breakdown: {report.split_counts}")
    print(f"Unique Signers:   {len(report.signer_ids)}")
    print(f"Signer Leakage:   {report.signer_leakage_detected}")
    if report.signer_leakage_detected:
        print(f"Leakage Details:  {report.signer_leakage_details}")
    if report.warnings:
        print("Warnings:")
        for w in report.warnings:
            print(f"  - ⚠️ {w}")
    if report.errors:
        print("Errors:")
        for e in report.errors:
            print(f"  - 🚨 {e}")
    print("=" * 60)


def cmd_manifest(args):
    adapter = get_adapter(args.dataset)
    path = Path(args.path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    task = TaskType(args.task) if args.task else None
    print(f"📝 Building manifest for {adapter.name} from {path}...")
    manifest = adapter.generate_manifest(path, output_path=output_path, task=task)
    print(f"✓ Manifest created: {output_path}")
    print(f"  Total Valid Samples: {manifest.total_samples}")
    print(f"  Task: {manifest.task}")
    print(f"  Splits: {manifest.splits}")
    print(f"  Vocabulary Size: {len(manifest.label_vocab)}")


def cmd_train(args):
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    print(f"⚙️ Loading training config from {config_path}...")
    config = TrainingConfig.load(config_path)

    # Allow CLI overrides
    if args.epochs:
        config.epochs = args.epochs
    if args.batch_size:
        config.batch_size = args.batch_size

    from backend.app.services.training_service import training_service
    print(f"🚀 Starting training job for {config.model_id} (Task: {config.task})...")
    job = training_service.start_training_job(config)

    # Monitor synchronously
    while job.state == "running":
        time_elapsed = int(job.to_dict()["duration_seconds"])
        print(f"\r[Epoch {job.current_epoch}/{job.total_epochs}] Train Loss: {job.train_loss:.4f} | Val Acc: {job.val_acc:.4f} ({time_elapsed}s)", end="")
        import time
        time.sleep(1)

    print(f"\nFinal State: {job.state.upper()}")
    if job.result:
        print(f"Checkpoint Saved: {job.result.get('checkpoint_path')}")


def cmd_models(args):
    registry = LocalModelRegistry()
    models = registry.list_models()
    print("=" * 75)
    print(f"{'MODEL ID':<25} {'TASK':<22} {'ARCH':<20} {'CLASSES'}")
    print("=" * 75)
    for m in models:
        active_tag = " [ACTIVE]" if m.is_active_for_task else ""
        print(f"{m.model_id + active_tag:<25} {m.task:<22} {m.architecture:<20} {m.num_classes}")
    print("=" * 75)


def cmd_serve(args):
    import uvicorn
    print(f"🤟 Starting SignSpeak server on {args.host}:{args.port}...")
    uvicorn.run("backend.app.main:app", host=args.host, port=args.port, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(description="SignSpeak Extensible ML Platform CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect a supported dataset adapter contract")
    p_inspect.add_argument("--dataset", required=True, choices=list_adapters(), help="Adapter name")

    # Validate
    p_validate = subparsers.add_parser("validate", help="Validate a local dataset directory")
    p_validate.add_argument("--dataset", required=True, choices=list_adapters(), help="Adapter name")
    p_validate.add_argument("--path", required=True, help="Path to local dataset directory")

    # Manifest
    p_manifest = subparsers.add_parser("manifest", help="Generate versioned manifest from dataset")
    p_manifest.add_argument("--dataset", required=True, choices=list_adapters())
    p_manifest.add_argument("--path", required=True)
    p_manifest.add_argument("--output", required=True, help="Destination manifest path (.json)")
    p_manifest.add_argument("--task", choices=[t.value for t in TaskType], default="isolated_sign")

    # Train
    p_train = subparsers.add_parser("train", help="Train a model using a training config JSON")
    p_train.add_argument("--config", required=True, help="Path to TrainingConfig JSON")
    p_train.add_argument("--epochs", type=int, help="Override epochs")
    p_train.add_argument("--batch-size", type=int, help="Override batch size")

    # Models
    p_models = subparsers.add_parser("models", help="List registered models in model registry")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Start the SignSpeak FastAPI microservice")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")

    args = parser.parse_args()

    dispatch = {
        "inspect": cmd_inspect,
        "validate": cmd_validate,
        "manifest": cmd_manifest,
        "train": cmd_train,
        "models": cmd_models,
        "serve": cmd_serve
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
