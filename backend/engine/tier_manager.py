"""TierManager for dynamic tier promotion/demotion - Phase 12"""
import logging
from typing import Optional, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .base_country import BaseCountry

logger = logging.getLogger(__name__)


class TierManager:
    """
    Manages dynamic tier changes for countries.

    Countries can be promoted (tier decreases) or demoted (tier increases)
    based on their stats. Hysteresis prevents oscillations:
    - Promotion: 3 consecutive ticks above threshold
    - Demotion: 5 consecutive ticks below threshold
    """

    # Thresholds for each tier
    TIER_THRESHOLDS = {
        1: {"min_power": 85, "min_military": 80, "nuclear_required": True},
        2: {"min_power": 65, "min_military": 55, "nuclear_required": False},
        3: {"min_power": 45, "min_military": 35, "nuclear_required": False},
        4: {"min_power": 25, "min_military": 15, "nuclear_required": False},
        5: {"min_power": 10, "min_military": 0, "nuclear_required": False},
        6: {"min_power": 0, "min_military": 0, "nuclear_required": False},
    }

    # AI levels and processing frequency by tier
    AI_CONFIG = {
        1: {"ai_level": "full", "process_frequency": 1},
        2: {"ai_level": "full", "process_frequency": 1},
        3: {"ai_level": "standard", "process_frequency": 1},
        4: {"ai_level": "simplified", "process_frequency": 2},
        5: {"ai_level": "minimal", "process_frequency": 3},
        6: {"ai_level": "passive", "process_frequency": 5},
    }

    # Hysteresis counters
    PROMOTION_THRESHOLD = 3  # Ticks above to promote
    DEMOTION_THRESHOLD = 5   # Ticks below to demote

    @classmethod
    def calculate_natural_tier(cls, country: "BaseCountry") -> int:
        """
        Calculate the tier a country should naturally be based on stats.

        Returns the natural tier (1-6) based on power score and military.
        """
        power = country.power_score
        military = country.military or 0
        has_nuclear = country.is_nuclear_power()

        # Check each tier from highest to lowest
        for tier in range(1, 7):
            thresholds = cls.TIER_THRESHOLDS[tier]

            meets_power = power >= thresholds["min_power"]
            meets_military = military >= thresholds["min_military"]
            meets_nuclear = not thresholds["nuclear_required"] or has_nuclear

            if meets_power and meets_military and meets_nuclear:
                return tier

        return 6  # Default to lowest tier

    @classmethod
    def check_tier_change(cls, country: "BaseCountry") -> Optional[int]:
        """
        Check if a country should change tier.

        Uses hysteresis to prevent oscillations:
        - Must be 3 ticks above threshold for promotion
        - Must be 5 ticks below threshold for demotion

        Returns new tier if change should happen, None otherwise.
        """
        natural_tier = cls.calculate_natural_tier(country)
        current_tier = country.tier

        if natural_tier == current_tier:
            # Reset stability counter when at natural tier
            country.tier_stability_counter = 0
            return None

        # Big jump (2+ tiers) = immediate change
        if abs(natural_tier - current_tier) >= 2:
            logger.info(
                f"{country.id}: Major tier change {current_tier} -> {natural_tier} "
                f"(power={country.get_power_score()})"
            )
            return natural_tier

        # Promotion (lower tier = more powerful)
        if natural_tier < current_tier:
            country.tier_stability_counter += 1
            if country.tier_stability_counter >= cls.PROMOTION_THRESHOLD:
                logger.info(
                    f"{country.id}: Promoted {current_tier} -> {natural_tier} "
                    f"(counter={country.tier_stability_counter})"
                )
                return natural_tier

        # Demotion (higher tier = less powerful)
        elif natural_tier > current_tier:
            country.tier_stability_counter += 1
            if country.tier_stability_counter >= cls.DEMOTION_THRESHOLD:
                logger.info(
                    f"{country.id}: Demoted {current_tier} -> {natural_tier} "
                    f"(counter={country.tier_stability_counter})"
                )
                return natural_tier

        return None

    @classmethod
    def apply_tier_change(cls, country: "BaseCountry", new_tier: int) -> dict:
        """
        Apply a tier change to a country.

        Updates tier, AI level, and processing frequency.
        Returns an event dict for the game log.
        """
        old_tier = country.tier
        country.tier = new_tier

        # Update AI configuration
        config = cls.AI_CONFIG.get(new_tier, cls.AI_CONFIG[6])
        country.ai_level = config["ai_level"]
        country.process_frequency = config["process_frequency"]

        # Reset stability counter
        country.tier_stability_counter = 0

        # Create event
        if new_tier < old_tier:
            return {
                "type": "tier_promotion",
                "country_id": country.id,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "title": f"{country.name} rises to Tier {new_tier}",
                "title_fr": f"{country.name_fr} devient une puissance de rang {new_tier}",
            }
        else:
            return {
                "type": "tier_demotion",
                "country_id": country.id,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "title": f"{country.name} falls to Tier {new_tier}",
                "title_fr": f"{country.name_fr} perd son statut (tier {old_tier} -> {new_tier})",
            }

    @classmethod
    def process_tier_changes(
        cls,
        countries: Dict[str, "BaseCountry"],
        tick_number: int
    ) -> List[dict]:
        """
        Process tier changes for all countries.

        Called periodically (every 5 ticks recommended) to check for
        tier promotions/demotions.

        Returns list of events for any tier changes.
        """
        events = []

        for country in countries.values():
            new_tier = cls.check_tier_change(country)
            if new_tier is not None:
                event = cls.apply_tier_change(country, new_tier)
                events.append(event)

        return events

    @classmethod
    def promote_by_player_focus(
        cls,
        countries: Dict[str, "BaseCountry"],
        focus_region: str,
        max_promotions: int = 3
    ) -> List[dict]:
        """
        Promote countries in a region the player is focusing on.

        This allows smaller countries to become more relevant when
        the player is active in their region.
        """
        events = []

        # Get tier 5-6 countries in the region, sorted by power
        candidates = [
            c for c in countries.values()
            if c.region == focus_region and c.tier >= 5
        ]
        candidates.sort(key=lambda c: c.get_power_score(), reverse=True)

        promoted = 0
        for country in candidates:
            if promoted >= max_promotions:
                break

            # Only promote one tier at a time
            new_tier = country.tier - 1
            if new_tier >= 4:  # Don't promote past tier 4 automatically
                event = cls.apply_tier_change(country, new_tier)
                event["reason"] = "player_focus"
                events.append(event)
                promoted += 1
                logger.info(
                    f"{country.id}: Promoted due to player focus in {focus_region}"
                )

        return events

    @classmethod
    def get_tier_stats(cls, countries: Dict[str, "BaseCountry"]) -> dict:
        """Get statistics about tier distribution."""
        stats = {tier: 0 for tier in range(1, 7)}
        for country in countries.values():
            stats[country.tier] += 1
        return stats
