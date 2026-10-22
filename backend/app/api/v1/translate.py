"""
Translation API Endpoint
Processes natural language text, applies normalization/tokenization,
and translates tokens to sign language media representations.
"""

from fastapi import APIRouter, HTTPException, status
from backend.app.models.schemas import TranslateRequest, TranslateResponse, TokenItem
from backend.app.services.text_processor import text_processor
from backend.app.services.translator_service import translator_service

router = APIRouter(tags=["Translation"])

@router.post("/translate", response_model=TranslateResponse)
def translate_text(payload: TranslateRequest):
    """
    Translate text into sign language representations.
    Supports English & Hindi transliteration mapped to ASL or ISL.
    """
    raw_text = payload.text.strip()
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Input text cannot be blank or whitespace."
        )

    # 1. Process text through NLP pipeline
    processed = text_processor.process(raw_text)

    # 2. Resolve tokens to sign objects via translator service
    signs = translator_service.translate(processed["tokens"], language=payload.language)

    # 3. Format token items
    token_models = [
        TokenItem(
            type=t["type"],
            value=t["value"],
            words=t.get("words")
        )
        for t in processed["tokens"]
    ]

    return TranslateResponse(
        original=processed["original"],
        normalized=processed["normalized"],
        tokens=token_models,
        signs=signs,
        source="backend"
    )
