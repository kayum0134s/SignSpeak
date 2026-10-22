"""
End-to-End System Integrity Tests for SignSpeak
Validates project architecture, file existence, and asset consistency.
"""

import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_project_structure_exists():
    expected_paths = [
        PROJECT_ROOT / "frontend" / "index.html",
        PROJECT_ROOT / "frontend" / "assets" / "css" / "styles.css",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "app.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "components" / "mediaPlayer.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "components" / "speechRecognition.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "components" / "mediaGenerator.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "services" / "apiService.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "services" / "signTranslator.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "utils" / "textProcessor.js",
        PROJECT_ROOT / "frontend" / "assets" / "js" / "utils" / "config.js",
        PROJECT_ROOT / "frontend" / "assets" / "images",
        PROJECT_ROOT / "backend" / "app" / "main.py",
        PROJECT_ROOT / "backend" / "app" / "api" / "v1" / "translate.py",
        PROJECT_ROOT / "backend" / "app" / "services" / "text_processor.py",
        PROJECT_ROOT / "backend" / "app" / "services" / "translator_service.py",
        PROJECT_ROOT / "backend" / "requirements.txt",
        PROJECT_ROOT / "data" / "sign-mapping.json",
        PROJECT_ROOT / "scripts" / "organize_videos.py",
        PROJECT_ROOT / "scripts" / "convert_videos_to_images.py",
        PROJECT_ROOT / "scripts" / "extract_asl.py",
        PROJECT_ROOT / "scripts" / "setup_kaggle_dataset.py",
        PROJECT_ROOT / "scripts" / "server.py",
        PROJECT_ROOT / "docs" / "PRD.md",
        PROJECT_ROOT / "docs" / "TRD.md",
        PROJECT_ROOT / "docs" / "METHODOLOGY.md",
        PROJECT_ROOT / "docs" / "README.md",
        PROJECT_ROOT / "brain.md",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / ".env.example",
        PROJECT_ROOT / ".gitignore"
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing required file: {path}"

def test_sign_mapping_integrity():
    mapping_file = PROJECT_ROOT / "data" / "sign-mapping.json"
    with open(mapping_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "asl" in data
    assert "isl" in data
    assert len(data["asl"]) >= 26
    assert len(data["isl"]) >= 26

def test_alphabet_assets_present():
    alphabet_dir = PROJECT_ROOT / "frontend" / "public" / "media" / "signs" / "asl" / "alphabet"
    assert alphabet_dir.exists()

    letters = [chr(c) for c in range(ord('a'), ord('z') + 1)]
    for letter in letters:
        img_path = alphabet_dir / f"{letter}.jpg"
        assert img_path.exists(), f"Missing alphabet image: {img_path}"

def test_frontend_entry_point_links():
    index_html = PROJECT_ROOT / "frontend" / "index.html"
    content = index_html.read_text(encoding="utf-8")
    assert 'assets/css/styles.css' in content
    assert 'assets/js/app.js' in content
    assert 'type="module"' in content

def test_phrase_videos_present():
    phrases_dir = PROJECT_ROOT / "frontend" / "public" / "media" / "signs" / "asl" / "phrases"
    assert phrases_dir.exists()
    expected_phrases = [
        "Friday.mp4", "Good Evening.mp4", "Good morning.mp4",
        "Have a good day.mp4", "How are you.mp4", "Monday.mp4",
        "Saturday.mp4", "Sunday.mp4", "Thursday.mp4",
        "Tuesday.mp4", "Wednesday.mp4", "What are you doing.mp4",
        "what is your name.mp4"
    ]
    for phrase in expected_phrases:
        video_path = phrases_dir / phrase
        assert video_path.exists(), f"Missing phrase video: {video_path}"

def test_fastapi_e2e_serving():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    
    # Root serves index.html
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "SignSpeak" in res_root.text

    # Assets serving
    res_css = client.get("/assets/css/styles.css")
    assert res_css.status_code == 200

    res_js = client.get("/assets/js/app.js")
    assert res_js.status_code == 200

    # Data serving
    res_data = client.get("/data/sign-mapping.json")
    assert res_data.status_code == 200

    # Media serving
    res_media = client.get("/public/media/signs/asl/alphabet/a.jpg")
    assert res_media.status_code == 200

