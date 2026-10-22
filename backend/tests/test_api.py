"""
Integration Tests for FastAPI Endpoints
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["total_asl_signs"] > 0

def test_v1_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_translate_endpoint_success():
    payload = {
        "text": "Good morning my friend",
        "language": "asl"
    }
    res = client.post("/api/v1/translate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "good morning" in data["normalized"]
    assert len(data["tokens"]) > 0
    assert len(data["signs"]) > 0
    assert data["source"] == "backend"

def test_translate_hindi_transliteration():
    payload = {
        "text": "namaste aapka naam kya hai",
        "language": "isl"
    }
    res = client.post("/api/v1/translate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "what is your name" in data["normalized"]
    assert any(s["tokenType"] == "phrase" for s in data["signs"])

def test_translate_empty_validation():
    payload = {"text": "   ", "language": "asl"}
    res = client.post("/api/v1/translate", json=payload)
    assert res.status_code == 422

def test_get_sign_mappings():
    res = client.get("/api/v1/signs/mappings?language=asl")
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "asl"
    assert "good morning" in data["signs"]

def test_get_phrases():
    res = client.get("/api/v1/signs/phrases?language=asl")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    phrase_names = [p["phrase"] for p in data["phrases"]]
    assert "good morning" in phrase_names

def test_get_alphabet():
    res = client.get("/api/v1/signs/alphabet?language=asl")
    assert res.status_code == 200
    data = res.json()
    assert len(data["alphabet"]) == 26
    assert "a" in data["alphabet"]
