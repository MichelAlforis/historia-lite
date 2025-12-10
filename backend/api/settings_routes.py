"""Settings and Ollama routes for Historia Lite"""
import logging
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from engine.tick_ollama import process_tick_with_ollama
from schemas.game import EventResponse, TickResponse
from api.game_state import (
    get_world,
    get_event_pool,
    get_ollama,
    get_settings,
    update_settings,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])


class SettingsResponse(BaseModel):
    ai_mode: str
    ollama_url: str
    ollama_model: str
    ollama_tiers: List[int]
    ollama_available: bool


class SettingsUpdate(BaseModel):
    ai_mode: Optional[str] = None
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_tiers: Optional[List[int]] = None


@router.get("/settings", response_model=SettingsResponse)
async def get_settings_endpoint():
    """Get current game settings including AI mode"""
    settings = get_settings()
    ollama = get_ollama()
    ollama_ok = await ollama.check_connection()

    return SettingsResponse(
        ai_mode=settings.ai_mode,
        ollama_url=settings.ollama_url,
        ollama_model=settings.ollama_model,
        ollama_tiers=settings.ollama_tiers,
        ollama_available=ollama_ok
    )


@router.post("/settings", response_model=SettingsResponse)
async def update_settings_endpoint(update: SettingsUpdate):
    """Update game settings"""
    if update.ai_mode is not None:
        if update.ai_mode not in ("algorithmic", "ollama"):
            raise HTTPException(
                status_code=400,
                detail="ai_mode must be 'algorithmic' or 'ollama'"
            )

    settings = update_settings(
        ai_mode=update.ai_mode,
        ollama_url=update.ollama_url,
        ollama_model=update.ollama_model,
        ollama_tiers=update.ollama_tiers
    )

    ollama = get_ollama()
    ollama_ok = await ollama.check_connection()

    return SettingsResponse(
        ai_mode=settings.ai_mode,
        ollama_url=settings.ollama_url,
        ollama_model=settings.ollama_model,
        ollama_tiers=settings.ollama_tiers,
        ollama_available=ollama_ok
    )


@router.get("/ollama/status")
async def check_ollama_status():
    """Check Ollama connection and list available models"""
    settings = get_settings()
    ollama = get_ollama()
    is_connected = await ollama.check_connection()
    models = await ollama.list_models() if is_connected else []

    return {
        "connected": is_connected,
        "url": settings.ollama_url,
        "current_model": settings.ollama_model,
        "available_models": models
    }


@router.post("/tick/ollama", response_model=TickResponse)
async def advance_tick_with_ollama():
    """Advance simulation using Ollama AI for major powers"""
    settings = get_settings()
    world = get_world()
    event_pool = get_event_pool()
    ollama = get_ollama()

    if not await ollama.check_connection():
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not available at {settings.ollama_url}"
        )

    old_year = world.year

    events = await process_tick_with_ollama(
        world=world,
        event_pool=event_pool,
        ollama=ollama,
        ollama_tiers=settings.ollama_tiers
    )

    event_responses = [EventResponse.from_event(e) for e in events]

    ai_decisions = len([e for e in events if e.type == "ai_decision"])
    decisions = len([e for e in events if e.type == "decision"])
    crises = len([e for e in events if e.type == "crisis"])

    summary = f"Year {old_year}: {ai_decisions} AI decisions, {decisions} algo decisions, {crises} crises"
    summary_fr = f"Annee {old_year}: {ai_decisions} decisions IA, {decisions} decisions algo, {crises} crises"

    logger.info(f"Ollama tick completed: {summary}")

    return TickResponse(
        year=world.year,
        events=event_responses,
        summary=summary,
        summary_fr=summary_fr
    )
