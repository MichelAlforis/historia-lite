"""Passive AI logic for Tier 6 countries (micro-states, territories)"""
import random
import logging
from typing import TYPE_CHECKING, List

from engine.country import Tier6Country
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World

logger = logging.getLogger(__name__)


def process_tier6_country(country: Tier6Country, world: "World") -> None:
    """
    Process a single Tier 6 country.
    Tier 6 countries are passive - they follow their protector's alignment
    and have minimal autonomous behavior.
    """
    # 1. Follow protector's geopolitical stance
    if country.protector:
        protector = world.get_any_country(country.protector)
        if protector:
            # Tier 6 stability is capped relative to protector
            if hasattr(protector, 'stability'):
                max_stability = protector.stability + 10
                country.stability = min(country.stability, max_stability)

    # 2. Minor stability drift
    # Micro-states are generally stable but can have small fluctuations
    drift = random.randint(-2, 3)  # Slight positive bias
    country.stability = max(20, min(100, country.stability + drift))

    # 3. Economic drift based on special status
    if country.special_status == "tax_haven":
        # Tax havens benefit from global instability
        if world.global_tension > 50:
            country.economy = min(100, country.economy + 1)
    elif country.special_status == "tourism":
        # Tourism suffers from global instability
        if world.global_tension > 60:
            country.economy = max(20, country.economy - 1)
        else:
            country.economy = min(100, country.economy + 1)
    elif country.special_status == "strategic_base":
        # Strategic bases are stable
        country.stability = max(country.stability, 60)


def process_tier6_countries(world: "World", tick_counter: int) -> List[Event]:
    """
    Process all Tier 6 countries in bulk.
    Only processes every 5 ticks to minimize computation.
    Tier 6 countries never generate events (too small to matter).

    Args:
        world: The world state
        tick_counter: Current tick count

    Returns:
        Empty list (Tier 6 never generates events)
    """
    # Only process when tick_counter % 5 == 0
    if tick_counter % 5 != 0:
        return []

    for country in world.tier6_countries.values():
        process_tier6_country(country, world)

    logger.info(f"Bulk processed {len(world.tier6_countries)} Tier 6 countries")
    return []


def get_protector_influence(country: Tier6Country, world: "World") -> dict:
    """
    Get influence information for a Tier 6 country based on its protector.
    Useful for displaying in UI.
    """
    if not country.protector:
        return {
            "has_protector": False,
            "alignment": 0,
            "alignment_label": "neutral"
        }

    protector = world.get_any_country(country.protector)
    if not protector:
        return {
            "has_protector": False,
            "alignment": 0,
            "alignment_label": "neutral"
        }

    # Determine alignment based on protector
    if country.protector in ("USA", "GBR", "FRA", "DEU", "AUS", "NZL", "CAN", "JPN"):
        alignment = -50  # Pro-West
        alignment_label = "pro_west"
    elif country.protector in ("CHN", "RUS"):
        alignment = 50  # Pro-East
        alignment_label = "pro_east"
    else:
        alignment = 0
        alignment_label = "neutral"

    return {
        "has_protector": True,
        "protector_id": country.protector,
        "protector_name": protector.name if hasattr(protector, 'name') else country.protector,
        "alignment": alignment,
        "alignment_label": alignment_label
    }
