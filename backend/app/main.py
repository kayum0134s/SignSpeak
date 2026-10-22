"""
SignSpeak Backend Application
FastAPI application serving REST API endpoints, health diagnostics,
and static frontend/media assets.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure SignSpeak project root is always in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from backend.app.utils.config import (
    CORS_ORIGINS,
    DEBUG,
    FRONTEND_DIR,
    MEDIA_DIR,
    PROJECT_ROOT
)
from backend.app.api.v1 import api_v1_router
from backend.app.services.translator_service import translator_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure mappings are loaded
    loaded = translator_service.load_mappings()
    stats = translator_service.get_stats()
    print("=" * 60)
    print("🤟 SignSpeak FastAPI Backend Initialized")
    print(f"📊 ASL Signs Loaded: {stats['total_asl_signs']}")
    print(f"📊 ISL Signs Loaded: {stats['total_isl_signs']}")
    print("=" * 60)
    yield
    print("👋 SignSpeak Backend Shutdown Cleanly.")

app = FastAPI(
    title="SignSpeak API",
    description="Deterministic Speech/Text to Sign Language Translation Microservice",
    version="2.0.0",
    debug=DEBUG,
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_v1_router, prefix="/api/v1")

# Also alias root /health
@app.get("/health", tags=["Health"])
def root_health():
    from backend.app.api.v1.health import get_health
    return get_health()

# Static Mounts for Media & Frontend Assets
if MEDIA_DIR.exists():
    app.mount("/public/media", StaticFiles(directory=str(MEDIA_DIR)), name="public_media")
    app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

data_dir = PROJECT_ROOT / "data"
if data_dir.exists():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

# Mount Frontend Static Assets
if FRONTEND_DIR.exists():
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    public_dir = FRONTEND_DIR / "public"
    if public_dir.exists():
        app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "SignSpeak API is running. Access /docs for OpenAPI specifications."}

if __name__ == "__main__":
    import uvicorn
    from backend.app.utils.config import HOST, PORT
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=DEBUG)
