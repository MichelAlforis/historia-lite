"""Historia Lite - Main FastAPI Application"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

# Import route modules - simplified
from api.game_routes import router as game_router
from api.settings_routes import router as settings_router
from api.tier4_routes import router as tier4_router
from api.tier5_routes import router as tier5_router
from api.tier6_routes import router as tier6_router
from api.player_routes import router as player_router
from api.blocs_routes import router as blocs_router
from api.currency_routes import router as currency_router
from api.influence_routes import router as influence_router
from api.saves_routes import router as saves_router
from api.scenarios_routes import router as scenarios_router
from api.scoring_routes import router as scoring_router
from api.espionage_routes import router as espionage_router
from api.regions_routes import router as regions_router
from api.economy_routes import router as economy_router
from api.ai_advisor_routes import router as ai_advisor_router
from api.timeline_routes import router as timeline_router  # NEW: Timeline API
from api.leaders_routes import router as leaders_router  # Leaders & Traits
from api.stats_routes import router as stats_router      # Historical Stats
from api.achievements_routes import router as achievements_router  # Achievements

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

# Include API routes - simplified
app.include_router(game_router)
app.include_router(settings_router)
app.include_router(tier4_router)
app.include_router(tier5_router)
app.include_router(tier6_router)
app.include_router(player_router)
app.include_router(blocs_router)
app.include_router(currency_router)
app.include_router(influence_router)
app.include_router(saves_router)
app.include_router(scenarios_router)
app.include_router(scoring_router)
app.include_router(espionage_router)
app.include_router(regions_router)
app.include_router(economy_router)
app.include_router(ai_advisor_router)
app.include_router(timeline_router)  # NEW: Timeline API
app.include_router(leaders_router)   # Leaders & Traits
app.include_router(stats_router)     # Historical Stats
app.include_router(achievements_router)  # Achievements


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Historia Lite",
        "version": "0.3.0",
        "description": "Simulateur geopolitique moderne - Version simplifiee avec Timeline",
        "endpoints": {
            "state": "/api/state",
            "tick": "/api/tick (monthly)",
            "tick_year": "/api/tick/year (annual - legacy)",
            "reset": "/api/reset",
            "country": "/api/country/{id}",
            "events": "/api/events",
            "timeline": "/api/timeline/*",
            "blocs": "/api/blocs",
            "currency": "/api/currency/*",
            "influence": "/api/influence/*",
            "saves": "/api/saves/*",
            "scenarios": "/api/scenarios/*",
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
