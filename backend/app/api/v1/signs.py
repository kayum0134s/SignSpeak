"""
Sign Registry & Discovery Endpoints
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.services.translator_service import translator_service

router = APIRouter(tags=["Signs"])

@router.get("/signs/mappings")
def get_sign_mappings(language: str = Query("asl", pattern="^(asl|isl)$")):
    """Get the full mapping dictionary for a given language."""
    target_lang = language.lower()
    mapping = translator_service.mappings.get(target_lang)
    if mapping is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{language}' not recognized."
        )
    return {
        "language": target_lang,
        "total_signs": len(mapping),
        "signs": mapping
    }

@router.get("/signs/phrases")
def get_phrases(language: str = Query("asl", pattern="^(asl|isl)$")):
    """List all recognized multi-word phrases for the given dialect."""
    target_lang = language.lower()
    mapping = translator_service.mappings.get(target_lang, {})
    phrases = [
        {"phrase": key, **val}
        for key, val in mapping.items()
        if " " in key or val.get("type") == "video"
    ]
    return {
        "language": target_lang,
        "count": len(phrases),
        "phrases": phrases
    }

@router.get("/signs/alphabet")
def get_alphabet(language: str = Query("asl", pattern="^(asl|isl)$")):
    """List all 26 alphabet letters and asset paths."""
    target_lang = language.lower()
    mapping = translator_service.mappings.get(target_lang, {})
    letters = {
        chr(c): mapping.get(chr(c), {})
        for c in range(ord('a'), ord('z') + 1)
    }
    return {
        "language": target_lang,
        "alphabet": letters
    }
