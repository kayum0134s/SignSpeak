"""
Pydantic Data Models & Validation Schemas for SignSpeak Backend API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TokenItem(BaseModel):
    type: str = Field(..., description="Token classification: 'phrase', 'word', or 'letter'")
    value: str = Field(..., description="Token textual content")
    words: Optional[List[str]] = Field(None, description="Constituent words for multi-word phrases")

class SignItem(BaseModel):
    type: str = Field(..., description="Media type: 'video' or 'image'")
    path: str = Field(..., description="Relative or absolute asset path")
    label: str = Field(..., description="Display label for the sign")
    tokenType: str = Field(..., description="'phrase', 'word', or 'letter'")
    language: str = Field("asl", description="'asl' or 'isl'")
    generated: bool = Field(False, description="Whether the asset was dynamically generated")

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Raw input text to translate")
    language: str = Field("asl", description="Target sign language: 'asl' or 'isl'")

class TranslateResponse(BaseModel):
    original: str
    normalized: str
    tokens: List[TokenItem]
    signs: List[SignItem]
    source: str = "backend"

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    total_asl_signs: int
    total_isl_signs: int
