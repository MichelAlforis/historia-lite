"""Historia Lite - Main FastAPI Application"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

# Import all route modules
from api.game_routes import router as game_router
from api.settings_routes import router as settings_router
from api.tier4_routes import router as tier4_router
from api.player_routes import router as player_router
from api.projects_routes import router as projects_router
from api.blocs_routes import router as blocs_router
from api.summits_routes import router as summits_router
from api.negotiations_routes import router as negotiations_router
from api.currency_routes import router as currency_router
from api.influence_routes import router as influence_router
from api.saves_routes import router as saves_router
from api.scenarios_routes import router as scenarios_router
from api.multiplayer_routes import router as multiplayer_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Historia Lite",
    description="Simulateur geopolitique moderne - Version Light",
    version="0.1.0",
)

# CORS middleware - Restrict to allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include API routes
app.include_router(game_router)
app.include_router(settings_router)
app.include_router(tier4_router)
app.include_router(player_router)
app.include_router(projects_router)
app.include_router(blocs_router)
app.include_router(summits_router)
app.include_router(negotiations_router)
app.include_router(currency_router)
app.include_router(influence_router)
app.include_router(saves_router)
app.include_router(scenarios_router)
app.include_router(multiplayer_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Historia Lite",
        "version": "0.1.0",
        "description": "Simulateur geopolitique moderne",
        "endpoints": {
            "state": "/api/state",
            "tick": "/api/tick",
            "reset": "/api/reset",
            "country": "/api/country/{id}",
            "events": "/api/events",
            "influence_zones": "/api/influence-zones",
            "superpowers": "/api/superpowers",
            "nuclear_powers": "/api/nuclear-powers",
            "blocs": "/api/blocs",
            "summits": "/api/summits",
            "negotiations": "/api/negotiations/*",
            "currency": "/api/currency/*",
            "influence": "/api/influence/*",
            "saves": "/api/saves/*",
            "scenarios": "/api/scenarios/*",
            "multiplayer": "/api/multiplayer/*",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
