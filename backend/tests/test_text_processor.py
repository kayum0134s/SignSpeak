"""
Unit Tests for Backend Text Processor
"""

import pytest
from backend.app.services.text_processor import TextProcessor

@pytest.fixture
def processor():
    return TextProcessor()

def test_cleaning(processor):
    raw = "Hello, World! 123...   Test???"
    cleaned = processor.clean(raw)
    assert cleaned == "hello world 123 test"

def test_contraction_expansion(processor):
    raw = "i'm happy and don't worry you're welcome"
    expanded = processor.expand_contractions(raw)
    assert "i am happy" in expanded
    assert "do not worry" in expanded
    assert "you are welcome" in expanded

def test_hindi_transliteration(processor):
    raw = "namaste aapka naam kya hai shukriya"
    translated = processor.translate_hindi(raw)
    assert "hello" in translated
    assert "what is your name" in translated
    assert "thank you" in translated

def test_greedy_tokenization_phrase(processor):
    raw = "good morning everyone"
    tokens = processor.tokenize(raw)
    assert len(tokens) == 2
    assert tokens[0]["type"] == "phrase"
    assert tokens[0]["value"] == "good morning"
    assert tokens[1]["type"] == "word"
    assert tokens[1]["value"] == "everyone"

def test_greedy_tokenization_multiple_phrases(processor):
    raw = "good morning and have a good day"
    tokens = processor.tokenize(raw)
    types = [t["type"] for t in tokens]
    values = [t["value"] for t in tokens]
    assert "good morning" in values
    assert "have a good day" in values
    assert "phrase" in types

def test_process_end_to_end(processor):
    res = processor.process("Aapka naam kya hai? I'm good!")
    assert res["original"] == "Aapka naam kya hai? I'm good!"
    assert "what is your name" in res["normalized"]
    assert "i am good" in res["normalized"]
    assert any(t["value"] == "what is your name" for t in res["tokens"])
