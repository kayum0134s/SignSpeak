"""
Integration tests for new ML platform API endpoints:
recognition, datasets, models, training, evaluation.
"""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)


def test_recognition_status():
    res = client.get("/api/v1/recognition/status")
    assert res.status_code == 200
    data = res.json()
    assert "ready" in data
    assert "active_model_id" in data
    assert "partial_transcript" in data
    assert "finalized_transcript" in data


def test_recognition_process_frame_and_reset():
    # Send empty 144-dim frame
    payload = {
        "landmarks": [0.0] * 144,
        "timestamp": 12345.67
    }
    res = client.post("/api/v1/recognition/process_frame", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data

    # Reset
    res_reset = client.post("/api/v1/recognition/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "ok"


def test_datasets_adapters():
    res = client.get("/api/v1/datasets/adapters")
    assert res.status_code == 200
    adapters = res.json()
    names = [a["name"].lower() for a in adapters]
    assert any("how2sign" in n for n in names)
    assert any("wlasl" in n for n in names)
    assert any("custom" in n for n in names)


def test_models_listing_and_selection():
    res = client.get("/api/v1/models/")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 1
    model_id = models[0]["model_id"]
    task = models[0]["task"]

    # Select model
    sel_res = client.post("/api/v1/models/select", json={"model_id": model_id, "task": task})
    assert sel_res.status_code == 200
    assert sel_res.json()["status"] == "ok"

    # Select with invalid task should return 400
    bad_res = client.post("/api/v1/models/select", json={"model_id": model_id, "task": "nonexistent_task"})
    assert bad_res.status_code in (400, 422)


def test_training_status():
    res = client.get("/api/v1/training/status")
    assert res.status_code == 200
    data = res.json()
    assert "state" in data
