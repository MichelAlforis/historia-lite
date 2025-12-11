"""Historia Lite - Game Engine"""
# Legacy imports (for backwards compatibility)
from .world import World
from .country import Country, Personality

# Phase 12: Unified architecture
from .base_country import BaseCountry
from .world_unified import UnifiedWorld, load_unified_world_from_json
from .tier_manager import TierManager

# Common imports
from .region import Region, InfluenceZone
from .tick import process_tick
from .tick_unified import process_unified_tick
from .events import Event, EventPool

__all__ = [
    # Legacy (backwards compatibility)
    "World",
    "Country",
    "Personality",
    # Phase 12: Unified
    "BaseCountry",
    "UnifiedWorld",
    "load_unified_world_from_json",
    "TierManager",
    # Phase 13: Unified tick
    "process_unified_tick",
    # Common
    "Region",
    "InfluenceZone",
    "process_tick",
    "Event",
    "EventPool",
]
