"""Global game state management for Historia Lite"""
import logging
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel

from config import settings as app_settings
from engine.world import World, load_world_from_json
from engine.events import EventPool
from ai.ollama_ai import OllamaAI

logger = logging.getLogger(__name__)

# Global game state
_world: Optional[World] = None
_event_pool: Optional[EventPool] = None
_ollama: Optional[OllamaAI] = None
_data_dir = Path(__file__).parent.parent / "data"


class GameSettings(BaseModel):
    """Game settings model"""
    ai_mode: str = "algorithmic"  # "algorithmic" or "ollama"
    ollama_url: str = app_settings.ollama_url
    ollama_model: str = app_settings.ollama_model
    ollama_tiers: List[int] = app_settings.ollama_tiers


_settings = GameSettings()


def get_world() -> World:
    """Get or initialize the world"""
    global _world, _event_pool
    if _world is None:
        _world = load_world_from_json(_data_dir)
        _event_pool = EventPool()
        logger.info(f"World initialized with {len(_world.countries)} countries")
    return _world


def get_event_pool() -> EventPool:
    """Get or initialize event pool"""
    global _event_pool
    if _event_pool is None:
        _event_pool = EventPool()
    return _event_pool


def get_ollama() -> OllamaAI:
    """Get or initialize Ollama AI client"""
    global _ollama
    if _ollama is None:
        _ollama = OllamaAI(
            base_url=_settings.ollama_url,
            model=_settings.ollama_model
        )
    return _ollama


def get_settings() -> GameSettings:
    """Get current game settings"""
    return _settings


def reset_world(seed: int = 42) -> World:
    """Reset the world to initial state"""
    global _world, _event_pool
    _world = load_world_from_json(_data_dir, seed=seed)
    _event_pool = EventPool()
    logger.info(f"World reset with seed {seed}")
    return _world


def update_settings(
    ai_mode: Optional[str] = None,
    ollama_url: Optional[str] = None,
    ollama_model: Optional[str] = None,
    ollama_tiers: Optional[List[int]] = None
) -> GameSettings:
    """Update game settings"""
    global _settings, _ollama

    if ai_mode is not None:
        _settings.ai_mode = ai_mode

    if ollama_url is not None:
        _settings.ollama_url = ollama_url
        _ollama = None  # Reset client to use new URL

    if ollama_model is not None:
        _settings.ollama_model = ollama_model
        _ollama = None  # Reset client to use new model

    if ollama_tiers is not None:
        _settings.ollama_tiers = ollama_tiers

    logger.info(f"Settings updated: mode={_settings.ai_mode}, model={_settings.ollama_model}")
    return _settings


def get_data_dir() -> Path:
    """Get the data directory path"""
    return _data_dir
