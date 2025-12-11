"""Global game state management for Historia Lite"""
import logging
from typing import Optional, List, Union
from pathlib import Path
from pydantic import BaseModel

from config import settings as app_settings
# Legacy world (backwards compatibility)
from engine.world import World, load_world_from_json
# Phase 12: Unified world
from engine.world_unified import UnifiedWorld, load_unified_world_from_json
from engine.events import EventPool
from engine.espionage import espionage_manager
from engine.resources import resource_manager
from engine.leaders import leader_manager
from engine.timeline import TimelineManager
from engine.crisis import CrisisManager
from engine.world import WorldMood
from ai.ollama_ai import OllamaAI

logger = logging.getLogger(__name__)

# Global game state - can be either legacy World or UnifiedWorld
_world: Optional[Union[World, UnifiedWorld]] = None
_event_pool: Optional[EventPool] = None
_timeline: Optional[TimelineManager] = None  # Timeline backbone
_crisis_manager: Optional[CrisisManager] = None  # Crisis manager (Phase 2)
_world_mood: Optional[WorldMood] = None  # World mood (Phase 2)
_ollama: Optional[OllamaAI] = None
_data_dir = Path(__file__).parent.parent / "data"
_use_unified: bool = False  # Set to True to use Phase 12 unified architecture


class GameSettings(BaseModel):
    """Game settings model"""
    ai_mode: str = "algorithmic"  # "algorithmic" or "ollama"
    ollama_url: str = app_settings.ollama_url
    ollama_model: str = app_settings.ollama_model
    ollama_tiers: List[int] = app_settings.ollama_tiers


_settings = GameSettings()


def _initialize_systems(world: World) -> None:
    """Initialize all game systems for the world"""
    global _timeline, _crisis_manager, _world_mood
    # Reset managers for new game using their reset() methods
    espionage_manager.reset()
    resource_manager.reset()
    leader_manager.reset()

    # Initialize timeline manager
    _timeline = TimelineManager()

    # Initialize crisis manager (Phase 2)
    _crisis_manager = CrisisManager()

    # Initialize world mood (Phase 2)
    _world_mood = WorldMood()

    logger.info("Game systems initialized (espionage, resources, leaders, timeline, crisis, mood)")


def get_world() -> Union[World, UnifiedWorld]:
    """Get or initialize the world"""
    global _world, _event_pool, _use_unified
    if _world is None:
        if _use_unified:
            _world = load_unified_world_from_json(_data_dir)
            logger.info(f"UnifiedWorld initialized with {len(_world.countries)} countries")
            logger.info(f"Tier distribution: {_world.get_tier_stats()}")
        else:
            _world = load_world_from_json(_data_dir)
            logger.info(f"Legacy World initialized with {len(_world.countries)} countries")
        _event_pool = EventPool()
        _initialize_systems(_world)
    return _world


def get_event_pool() -> EventPool:
    """Get or initialize event pool"""
    global _event_pool
    if _event_pool is None:
        _event_pool = EventPool()
    return _event_pool


def get_timeline() -> TimelineManager:
    """Get or initialize the timeline manager"""
    global _timeline
    if _timeline is None:
        _timeline = TimelineManager()
    return _timeline


def get_crisis_manager() -> CrisisManager:
    """Get or initialize the crisis manager (Phase 2)"""
    global _crisis_manager
    if _crisis_manager is None:
        _crisis_manager = CrisisManager()
    return _crisis_manager


def get_world_mood() -> WorldMood:
    """Get or initialize the world mood (Phase 2)"""
    global _world_mood
    if _world_mood is None:
        _world_mood = WorldMood()
    return _world_mood


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


def reset_world(seed: int = 42) -> Union[World, UnifiedWorld]:
    """Reset the world to initial state"""
    global _world, _event_pool, _timeline, _crisis_manager, _world_mood, _use_unified
    if _use_unified:
        _world = load_unified_world_from_json(_data_dir, seed=seed)
        logger.info(f"UnifiedWorld reset with seed {seed}")
    else:
        _world = load_world_from_json(_data_dir, seed=seed)
        logger.info(f"Legacy World reset with seed {seed}")
    _event_pool = EventPool()
    _timeline = TimelineManager()  # Reset timeline on world reset
    _crisis_manager = CrisisManager()  # Reset crisis manager
    _world_mood = WorldMood()  # Reset world mood
    _initialize_systems(_world)
    return _world


def set_unified_mode(enabled: bool = True) -> None:
    """Enable or disable unified architecture mode (Phase 12)"""
    global _use_unified, _world
    if _use_unified != enabled:
        _use_unified = enabled
        _world = None  # Force reload on next get_world()
        logger.info(f"Unified architecture mode: {'enabled' if enabled else 'disabled'}")


def is_unified_mode() -> bool:
    """Check if unified architecture mode is enabled"""
    return _use_unified


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


class _GameState:
    """Singleton game state accessor for compatibility"""

    @property
    def world(self) -> Optional[Union[World, UnifiedWorld]]:
        return _world

    @property
    def event_pool(self) -> Optional[EventPool]:
        return _event_pool

    @property
    def timeline(self) -> Optional[TimelineManager]:
        return _timeline

    @property
    def crisis_manager(self) -> Optional[CrisisManager]:
        return _crisis_manager

    @property
    def world_mood(self) -> Optional[WorldMood]:
        return _world_mood

    @property
    def is_unified(self) -> bool:
        return _use_unified


# Export singleton instance for scoring_routes compatibility
game_state = _GameState()
