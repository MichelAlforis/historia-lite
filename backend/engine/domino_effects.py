"""
Domino Effects - Wildcard zones can propagate importance

Option 2: Secondary zones can become critical through contagion effects.

Examples:
- Congo civil war 1960 -> threatens all of Africa
- Bay of Pigs failure -> Cuba becomes symbolic (even without missiles)
- Middle East crisis -> North Africa becomes strategic
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.narrative_state import NarrativeZone

logger = logging.getLogger(__name__)


# =============================================================================
# ADJACENT ZONES - DOMINO EFFECT MAP
# =============================================================================

# Which zones are "adjacent" for domino effect purposes
# A crisis in one zone increases importance of adjacent zones
ADJACENT_ZONES: dict[str, list[str]] = {
    # Americas
    "central_america": ["south_america"],  # Cuba effect spreads south
    "south_america": ["central_america", "africa_sub"],  # Trans-Atlantic influence

    # Europe
    "europe_west": ["europe_east", "scandinavia", "turkey_greece"],
    "europe_east": ["europe_west", "scandinavia", "turkey_greece"],
    "scandinavia": ["europe_west", "europe_east"],
    "turkey_greece": ["europe_west", "europe_east", "middle_east"],

    # Middle East & Africa
    "middle_east": ["north_africa", "south_asia", "turkey_greece"],
    "north_africa": ["middle_east", "africa_sub", "europe_west"],
    "africa_sub": ["north_africa", "south_america"],

    # Asia
    "south_asia": ["middle_east", "southeast_asia", "far_east"],
    "southeast_asia": ["south_asia", "far_east"],
    "far_east": ["southeast_asia", "south_asia"],
}


# =============================================================================
# WILDCARD EVENT TYPES
# =============================================================================

# Events that can transform a secondary zone into a critical one
WILDCARD_EVENTS = [
    "COV_COUP",       # Successful/failed coup
    "MIL_BLOCKADE",   # Military blockade
    "MIL_PROXY",      # Proxy war
    "MIL_BASE",       # New military base
    "nuclear_threat",  # Nuclear escalation
    "superpower_confrontation",  # Direct US-USSR clash
]


# =============================================================================
# DOMINO BONUS CALCULATION
# =============================================================================

def calculate_domino_bonus(zone_id: str, all_zones: dict[str, "NarrativeZone"]) -> int:
    """
    Calculate importance bonus from adjacent zones in crisis.

    Ex: If Middle East is in intense crisis, North Africa gains +2 importance

    Args:
        zone_id: ID of the zone to calculate bonus for
        all_zones: Dict of all zones in the game

    Returns:
        Bonus to add to strategic_value (capped at +3)
    """
    bonus = 0
    adjacent = ADJACENT_ZONES.get(zone_id, [])

    for adj_id in adjacent:
        adj_zone = all_zones.get(adj_id)
        if adj_zone and adj_zone.has_crisis:
            # Adjacent crisis = +1 to +2 based on intensity
            if adj_zone.crisis_intensity >= 50:
                bonus += 2  # Intense crisis
            else:
                bonus += 1  # Low-intensity crisis

    # Cap bonus at +3
    final_bonus = min(3, bonus)

    if final_bonus > 0:
        logger.debug(
            f"Domino effect: {zone_id} gets +{final_bonus} importance "
            f"from {len(adjacent)} adjacent zones"
        )

    return final_bonus


def check_wildcard_trigger(zone: "NarrativeZone", event_type: str) -> bool:
    """
    Check if an event transforms a secondary zone into a wildcard.

    Wildcards are low-importance zones that suddenly become critical
    due to major events (coups, blockades, nuclear threats).

    Args:
        zone: The zone where the event occurs
        event_type: Type of event (e.g., "COV_COUP", "MIL_BLOCKADE")

    Returns:
        True if zone should be treated as wildcard
    """
    # Already important zones can't be wildcards
    if zone.strategic_value >= 7:
        return False

    return event_type in WILDCARD_EVENTS


def get_regional_tension(zone_id: str, all_zones: dict[str, "NarrativeZone"]) -> int:
    """
    Calculate regional tension based on adjacent zone states.

    High regional tension = more volatile situation.

    Returns:
        Tension score 0-100
    """
    adjacent = ADJACENT_ZONES.get(zone_id, [])
    if not adjacent:
        return 0

    total_tension = 0
    crisis_count = 0

    for adj_id in adjacent:
        adj_zone = all_zones.get(adj_id)
        if adj_zone:
            # Add crisis intensity
            if adj_zone.has_crisis:
                total_tension += adj_zone.crisis_intensity
                crisis_count += 1

            # Add instability contribution
            instability = 100 - adj_zone.stability
            total_tension += instability // 2

    if not adjacent:
        return 0

    # Average and scale
    avg_tension = total_tension // len(adjacent)

    # Bonus for multiple simultaneous crises
    if crisis_count >= 2:
        avg_tension = min(100, avg_tension + 20)

    return avg_tension


def get_contagion_risk(zone: "NarrativeZone", all_zones: dict[str, "NarrativeZone"]) -> str:
    """
    Assess risk of crisis spreading to this zone.

    Returns:
        Risk level: "low", "medium", "high", "critical"
    """
    regional_tension = get_regional_tension(zone.id, all_zones)
    own_stability = zone.stability

    # Low stability + high regional tension = critical
    if own_stability < 30 and regional_tension >= 60:
        return "critical"

    if own_stability < 50 and regional_tension >= 50:
        return "high"

    if regional_tension >= 40 or own_stability < 40:
        return "medium"

    return "low"
