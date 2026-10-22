"""
Backend Configuration Module
Loads environment variables and system paths.
"""

import os
from pathlib import Path
from typing import List

# Base Directory Resolution
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Server Settings
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

# CORS Origins
raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://localhost:5500,*")
CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

# Data & Asset Paths
DATA_MAPPING_FILE: Path = PROJECT_ROOT / "data" / "sign-mapping.json"
FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"
MEDIA_DIR: Path = FRONTEND_DIR / "public" / "media"
if not MEDIA_DIR.exists():
    MEDIA_DIR = PROJECT_ROOT / "media"
