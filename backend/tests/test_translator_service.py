"""
Unit Tests for Translator Service
"""

import pytest
from backend.app.services.translator_service import translator_service

def test_mappings_loaded():
    assert len(translator_service.mappings.get("asl", {})) > 0
    assert len(translator_service.mappings.get("isl", {})) > 0

def test_translate_known_phrase():
    tokens = [{"type": "phrase", "value": "good morning", "words": ["good", "morning"]}]
    signs = translator_service.translate(tokens, language="asl")
    assert len(signs) >= 1
    assert signs[0].label == "good morning"
    assert signs[0].type == "video"
    assert "good morning" in signs[0].path.lower()

def test_translate_word_fingerspelling_fallback():
    # 'xyzq' is an unknown word that should trigger fingerspelling
    tokens = [{"type": "word", "value": "xyz"}]
    signs = translator_service.translate(tokens, language="asl")
    assert len(signs) == 3
    assert [s.label for s in signs] == ["X", "Y", "Z"]
    assert all(s.tokenType == "letter" for s in signs)
    assert all(s.type == "image" for s in signs)

def test_path_normalization():
    norm = translator_service.normalize_media_path("media/signs/asl/alphabet/a.jpg")
    assert norm == "public/media/signs/asl/alphabet/a.jpg"
