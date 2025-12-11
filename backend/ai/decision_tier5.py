"""Minimal AI decision logic for Tier 5 countries (batch processing by region)"""
import random
import logging
from typing import TYPE_CHECKING, List

from engine.country import Tier5Country
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World

logger = logging.getLogger(__name__)


# Regional trend modifiers based on world events
REGIONAL_MODIFIERS = {
    "africa": {"base_stability": -5, "alignment_drift": 5},  # Slight eastward drift
    "asia": {"base_stability": 0, "alignment_drift": 3},
    "latam": {"base_stability": -2, "alignment_drift": 0},
    "caribbean": {"base_stability": 0, "alignment_drift": -5},  # US influence
    "europe": {"base_stability": 5, "alignment_drift": -3},  # Generally stable, west-leaning
    "middle_east": {"base_stability": -5, "alignment_drift": 0},
    "oceania": {"base_stability": 3, "alignment_drift": -5},  # AUS/NZL influence
}


def calculate_regional_trend(region: str, world: "World") -> int:
    """
    Calculate the regional alignment trend based on major power activity.
    Returns alignment drift for countries in this region.
    """
    base_drift = REGIONAL_MODIFIERS.get(region, {}).get("alignment_drift", 0)

    # Global tension affects alignment volatility
    if world.global_tension > 70:
        base_drift += random.randint(-5, 5)

    # China's economic growth creates eastward pull globally
    china = world.countries.get("CHN")
    usa = world.countries.get("USA")
    if china and usa:
        economic_diff = china.economy - usa.economy
        if economic_diff > 10:
            base_drift += 3
        elif economic_diff < -10:
            base_drift -= 2

    return base_drift


def calculate_regional_stability(region: str, world: "World") -> int:
    """
    Calculate average stability for a region.
    Considers major regional powers and conflicts.
    """
    base_stability = 50

    # Check for conflicts in region
    for conflict in world.active_conflicts:
        if conflict.region == region:
            base_stability -= conflict.intensity * 2

    # Regional modifier
    base_stability += REGIONAL_MODIFIERS.get(region, {}).get("base_stability", 0)

    # Global tension affects stability
    if world.global_tension > 60:
        base_stability -= 5

    return max(20, min(80, base_stability))


def process_tier5_country(
    country: Tier5Country,
    regional_trend: int,
    regional_stability: int,
    world: "World"
) -> Event | None:
    """
    Process a single Tier 5 country.
    Tier 5 countries follow regional trends and have occasional crises.
    """
    event = None

    # 1. Follow regional alignment trend (with some randomness)
    alignment_shift = regional_trend + random.randint(-3, 3)
    if alignment_shift != 0:
        country.shift_alignment(int(alignment_shift * 0.3))

    # 2. Stability follows regional stability (weighted average)
    stability_diff = regional_stability - country.stability
    country.stability = min(100, max(0, country.stability + int(stability_diff * 0.2)))

    # 3. Minor economic growth/decline based on stability
    if country.stability > 50:
        country.economy = min(100, country.economy + random.randint(0, 1))
    elif country.stability < 30:
        country.economy = max(0, country.economy - random.randint(0, 2))

    # 4. Crisis check (rare, 2% base chance)
    if not country.in_crisis:
        crisis_chance = 0.02
        if country.stability < 30:
            crisis_chance += 0.05
        if country.economy < 20:
            crisis_chance += 0.03

        if random.random() < crisis_chance:
            country.in_crisis = True
            country.crisis_type = random.choice(["famine", "civil_unrest", "economic_collapse"])
            country.stability = max(0, country.stability - 15)
            country.economy = max(0, country.economy - 10)

            event = Event(
                id=f"tier5_crisis_{world.year}_{country.id}",
                year=world.year,
                type="tier5_crisis",
                title=f"Crisis in {country.name}",
                title_fr=f"Crise en {country.name_fr}",
                description=f"{country.name} experiences {country.crisis_type.replace('_', ' ')}",
                description_fr=f"{country.name_fr} connait une {_translate_crisis(country.crisis_type)}",
                country_id=country.id
            )
            logger.info(f"Crisis in Tier 5 country {country.id}: {country.crisis_type}")

    # 5. Crisis recovery (40% chance each processed tick)
    elif random.random() < 0.4:
        country.in_crisis = False
        country.crisis_type = None
        country.stability = min(100, country.stability + 5)

    return event


def _translate_crisis(crisis_type: str) -> str:
    """Translate crisis type to French"""
    translations = {
        "famine": "famine",
        "civil_unrest": "troubles civils",
        "economic_collapse": "effondrement economique",
        "coup": "coup d'etat"
    }
    return translations.get(crisis_type, "crise")


def process_tier5_countries(world: "World", tick_counter: int) -> List[Event]:
    """
    Process all Tier 5 countries in batch by region.
    Only processes every 3 ticks to reduce computation.

    Args:
        world: The world state
        tick_counter: Current tick count

    Returns:
        List of events generated
    """
    events = []

    # Only process when tick_counter % 3 == 0
    if tick_counter % 3 != 0:
        return events

    # Group countries by region
    regions = {}
    for country in world.tier5_countries.values():
        if country.region not in regions:
            regions[country.region] = []
        regions[country.region].append(country)

    # Process each region as a batch
    for region, countries in regions.items():
        # Calculate regional metrics once per region
        regional_trend = calculate_regional_trend(region, world)
        regional_stability = calculate_regional_stability(region, world)

        # Process each country in region
        for country in countries:
            event = process_tier5_country(
                country, regional_trend, regional_stability, world
            )
            if event:
                events.append(event)

    logger.info(
        f"Processed {len(world.tier5_countries)} Tier 5 countries "
        f"in {len(regions)} regions, {len(events)} events"
    )
    return events
