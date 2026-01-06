"""
Action Cost Calculator - Dynamic Cost System for Historia

Calculates action costs based on:
1. Zone properties (strategic value, control, stability)
2. Action type (diplomacy, military, covert, etc.)
3. Context (DEFCON, world tension, relations)

NO MORE FLAT COSTS - Attacking China is NOT the same as influencing Belgium!
"""

import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class ActionCategory(str, Enum):
    DIPLOMACY = "diplomacy"
    MILITARY = "military"
    COVERT = "covert"
    INTEL = "intel"
    ECONOMIC = "economic"
    DOMESTIC = "domestic"


# Base costs by intention type (baseline, modified by context)
BASE_COSTS: dict[str, int] = {
    # Diplomacy - relatively cheap but outcomes vary
    "DIPLO_ALLIANCE": 8,
    "DIPLO_THREAT": 12,
    "DIPLO_NEGOTIATE": 6,
    "DIPLO_CONCEDE": 4,
    "DIPLO_SANCTION": 10,
    "DIPLO_SUMMIT": 15,
    "DIPLO_BACKCHANNEL": 8,

    # Military - expensive, high stakes
    "MIL_REINFORCE": 18,
    "MIL_WITHDRAW": 5,
    "MIL_DEMO": 20,
    "MIL_PROXY": 25,
    "MIL_BLOCKADE": 30,
    "MIL_BASE": 35,

    # Covert - medium cost, high risk
    "COV_DESTAB": 15,
    "COV_COUP": 40,
    "COV_SABOTAGE": 20,
    "COV_ASSASSIN": 50,
    "COV_PROPAGANDA": 10,

    # Intel - cheap but cumulative risk
    "INTEL_COLLECT": 5,
    "INTEL_VERIFY": 3,
    "INTEL_COUNTER": 8,
    "INTEL_DISINFO": 12,

    # Economic - moderate
    "ECO_AID": 12,
    "ECO_TRADE": 8,
    "ECO_EMBARGO": 15,
    "ECO_INVEST": 20,

    # Domestic - cheap (internal focus)
    "DOM_SPEECH": 3,
    "DOM_REFORM": 10,
    "DOM_REPRESS": 8,
    "DOM_ELECTION": 12,
}

# Category multipliers
CATEGORY_MULTIPLIERS: dict[ActionCategory, float] = {
    ActionCategory.DIPLOMACY: 1.0,
    ActionCategory.MILITARY: 1.4,
    ActionCategory.COVERT: 1.3,
    ActionCategory.INTEL: 0.9,
    ActionCategory.ECONOMIC: 1.1,
    ActionCategory.DOMESTIC: 0.7,
}

# Strategic value multipliers (zone importance)
STRATEGIC_VALUE_MULTIPLIERS: dict[int, float] = {
    1: 0.6,   # Unimportant backwater
    2: 0.7,
    3: 0.8,
    4: 0.9,
    5: 1.0,   # Average importance
    6: 1.1,
    7: 1.25,
    8: 1.4,
    9: 1.6,
    10: 2.0,  # Critical strategic zone
}

# DEFCON multipliers (higher alert = higher costs)
DEFCON_MULTIPLIERS: dict[int, float] = {
    5: 0.85,  # Peace - easier to act
    4: 1.0,   # Normal
    3: 1.15,  # Elevated
    2: 1.4,   # Crisis
    1: 1.8,   # War imminent - everything is costly
}

# Zone control modifiers
CONTROL_THRESHOLDS = {
    "dominated_by_us": (70, 100, 0.7),      # We control - cheap
    "strong_us": (50, 70, 0.85),            # Strong position
    "contested": (30, 50, 1.0),             # Contested - normal
    "weak_us": (10, 30, 1.2),               # Weak position - harder
    "hostile": (0, 10, 1.5),                # Enemy territory - very hard
}


# =============================================================================
# COST BREAKDOWN DATACLASS
# =============================================================================

@dataclass
class CostBreakdown:
    """Detailed breakdown of how cost was calculated."""
    base_cost: int
    intention_type: str
    zone_id: Optional[str]

    # Multipliers
    category_mult: float = 1.0
    strategic_value_mult: float = 1.0
    control_mult: float = 1.0
    stability_mult: float = 1.0
    defcon_mult: float = 1.0
    tension_mult: float = 1.0
    resources_mult: float = 1.0

    # Final
    final_cost: int = 0

    # Explanations
    explanations: list[str] = None

    def __post_init__(self):
        if self.explanations is None:
            self.explanations = []

    def to_dict(self) -> dict:
        return {
            "base_cost": self.base_cost,
            "intention_type": self.intention_type,
            "zone_id": self.zone_id,
            "multipliers": {
                "category": round(self.category_mult, 2),
                "strategic_value": round(self.strategic_value_mult, 2),
                "control": round(self.control_mult, 2),
                "stability": round(self.stability_mult, 2),
                "defcon": round(self.defcon_mult, 2),
                "tension": round(self.tension_mult, 2),
                "resources": round(self.resources_mult, 2),
            },
            "total_multiplier": round(self.get_total_multiplier(), 2),
            "final_cost": self.final_cost,
            "explanations": self.explanations,
        }

    def get_total_multiplier(self) -> float:
        return (
            self.category_mult *
            self.strategic_value_mult *
            self.control_mult *
            self.stability_mult *
            self.defcon_mult *
            self.tension_mult *
            self.resources_mult
        )


# =============================================================================
# MAIN CALCULATOR
# =============================================================================

class ActionCostCalculator:
    """
    Calculates dynamic costs for actions based on context.

    Usage:
        calculator = ActionCostCalculator()
        cost = calculator.calculate(
            intention_type="MIL_REINFORCE",
            zone=some_zone,
            defcon=3,
            world_tension=65
        )
    """

    def __init__(self):
        self.base_costs = BASE_COSTS
        self.category_multipliers = CATEGORY_MULTIPLIERS

    def get_category(self, intention_type: str) -> ActionCategory:
        """Determine action category from intention type."""
        prefix = intention_type.split("_")[0] if "_" in intention_type else intention_type
        mapping = {
            "DIPLO": ActionCategory.DIPLOMACY,
            "MIL": ActionCategory.MILITARY,
            "COV": ActionCategory.COVERT,
            "INTEL": ActionCategory.INTEL,
            "ECO": ActionCategory.ECONOMIC,
            "DOM": ActionCategory.DOMESTIC,
        }
        return mapping.get(prefix, ActionCategory.DIPLOMACY)

    def calculate(
        self,
        intention_type: str,
        zone: Optional["NarrativeZone"] = None,
        defcon: int = 4,
        world_tension: int = 50,
        player_influence_in_zone: Optional[int] = None,
        adversary_control_in_zone: Optional[int] = None,
    ) -> int:
        """Calculate final cost for an action."""
        breakdown = self.calculate_with_breakdown(
            intention_type=intention_type,
            zone=zone,
            defcon=defcon,
            world_tension=world_tension,
            player_influence_in_zone=player_influence_in_zone,
            adversary_control_in_zone=adversary_control_in_zone,
        )
        return breakdown.final_cost

    def calculate_with_breakdown(
        self,
        intention_type: str,
        zone: Optional["NarrativeZone"] = None,
        defcon: int = 4,
        world_tension: int = 50,
        player_influence_in_zone: Optional[int] = None,
        adversary_control_in_zone: Optional[int] = None,
    ) -> CostBreakdown:
        """Calculate cost with full breakdown for UI display."""

        # Base cost
        base_cost = self.base_costs.get(intention_type, 15)

        breakdown = CostBreakdown(
            base_cost=base_cost,
            intention_type=intention_type,
            zone_id=zone.id if zone else None,
        )

        # 1. Category multiplier
        category = self.get_category(intention_type)
        breakdown.category_mult = self.category_multipliers.get(category, 1.0)
        if breakdown.category_mult != 1.0:
            breakdown.explanations.append(
                f"Action {category.value}: x{breakdown.category_mult:.1f}"
            )

        # 2. Zone-based multipliers
        if zone:
            # Strategic value - USE DYNAMIC IMPORTANCE (Option 4)
            # get_effective_importance() returns context-adjusted value:
            # - Crisis bonus (+1 to +5)
            # - Instability bonus (+1)
            # - Contested zone bonus (+1)
            # - Domino effect bonus (+1 to +3)
            base_value = getattr(zone, "strategic_value", 5)
            if hasattr(zone, "get_effective_importance"):
                strategic_value = zone.get_effective_importance()
            else:
                strategic_value = base_value

            breakdown.strategic_value_mult = STRATEGIC_VALUE_MULTIPLIERS.get(
                strategic_value, 1.0
            )

            # Explanation shows both base and effective if different
            if strategic_value != base_value:
                breakdown.explanations.append(
                    f"Importance dynamique ({base_value}→{strategic_value}/10): x{breakdown.strategic_value_mult:.1f}"
                )
            elif strategic_value >= 7:
                breakdown.explanations.append(
                    f"Zone strategique ({strategic_value}/10): x{breakdown.strategic_value_mult:.1f}"
                )
            elif strategic_value <= 3:
                breakdown.explanations.append(
                    f"Zone secondaire ({strategic_value}/10): x{breakdown.strategic_value_mult:.1f}"
                )

            # Control situation
            our_control = player_influence_in_zone or getattr(zone, "control_us", 50)
            their_control = adversary_control_in_zone or getattr(zone, "control_ussr", 50)

            if our_control >= 70:
                breakdown.control_mult = 0.7
                breakdown.explanations.append("Territoire controle: x0.7")
            elif our_control >= 50:
                breakdown.control_mult = 0.85
                breakdown.explanations.append("Position forte: x0.85")
            elif their_control >= 70:
                breakdown.control_mult = 1.5
                breakdown.explanations.append("Territoire hostile: x1.5")
            elif their_control >= 50:
                breakdown.control_mult = 1.25
                breakdown.explanations.append("Position adverse forte: x1.25")

            # Stability
            stability = getattr(zone, "stability", 50)
            if stability < 30:
                breakdown.stability_mult = 1.3
                breakdown.explanations.append("Zone instable: x1.3")
            elif stability < 50:
                breakdown.stability_mult = 1.1
                breakdown.explanations.append("Zone fragile: x1.1")
            elif stability > 80:
                breakdown.stability_mult = 0.9
                breakdown.explanations.append("Zone stable: x0.9")

            # Strategic resources
            has_resources = getattr(zone, "has_strategic_resources", False)
            has_oil = getattr(zone, "has_oil", False)
            if has_resources or has_oil:
                breakdown.resources_mult = 1.15 if has_resources and has_oil else 1.1
                breakdown.explanations.append(
                    f"Ressources strategiques: x{breakdown.resources_mult:.2f}"
                )

        # 3. Global context multipliers

        # DEFCON
        breakdown.defcon_mult = DEFCON_MULTIPLIERS.get(defcon, 1.0)
        if defcon <= 2:
            breakdown.explanations.append(f"DEFCON {defcon} (crise): x{breakdown.defcon_mult:.1f}")
        elif defcon == 5:
            breakdown.explanations.append(f"DEFCON 5 (paix): x{breakdown.defcon_mult:.2f}")

        # World tension
        if world_tension >= 80:
            breakdown.tension_mult = 1.3
            breakdown.explanations.append("Tension mondiale critique: x1.3")
        elif world_tension >= 60:
            breakdown.tension_mult = 1.15
            breakdown.explanations.append("Tension mondiale elevee: x1.15")
        elif world_tension <= 25:
            breakdown.tension_mult = 0.85
            breakdown.explanations.append("Tension mondiale basse: x0.85")

        # Calculate final cost
        total_mult = breakdown.get_total_multiplier()
        breakdown.final_cost = max(1, round(base_cost * total_mult))

        logger.debug(
            f"Cost calculation: {intention_type} -> base={base_cost}, "
            f"mult={total_mult:.2f}, final={breakdown.final_cost}"
        )

        return breakdown


# =============================================================================
# RISK CALCULATOR (Companion to Cost)
# =============================================================================

class ActionRiskCalculator:
    """
    Calculates risk levels for actions.
    Higher risk = more unpredictable outcomes.
    """

    BASE_RISKS: dict[str, str] = {
        # Low risk
        "DIPLO_NEGOTIATE": "low",
        "DIPLO_SUMMIT": "low",
        "DIPLO_CONCEDE": "low",
        "DOM_SPEECH": "low",
        "INTEL_COLLECT": "low",

        # Medium risk
        "DIPLO_ALLIANCE": "medium",
        "DIPLO_SANCTION": "medium",
        "DIPLO_BACKCHANNEL": "medium",
        "MIL_REINFORCE": "medium",
        "MIL_WITHDRAW": "medium",
        "ECO_AID": "medium",
        "ECO_TRADE": "medium",
        "INTEL_VERIFY": "medium",

        # High risk
        "DIPLO_THREAT": "high",
        "MIL_DEMO": "high",
        "MIL_PROXY": "high",
        "MIL_BASE": "high",
        "COV_DESTAB": "high",
        "COV_PROPAGANDA": "high",
        "ECO_EMBARGO": "high",
        "INTEL_DISINFO": "high",
        "DOM_REPRESS": "high",

        # Extreme risk
        "MIL_BLOCKADE": "extreme",
        "COV_COUP": "extreme",
        "COV_SABOTAGE": "extreme",
        "COV_ASSASSIN": "extreme",
        "INTEL_COUNTER": "high",  # Can expose your network
    }

    def calculate(
        self,
        intention_type: str,
        zone: Optional["NarrativeZone"] = None,
        defcon: int = 4,
        world_tension: int = 50,
    ) -> str:
        """Calculate risk level: low, medium, high, extreme."""
        base_risk = self.BASE_RISKS.get(intention_type, "medium")
        risk_levels = ["low", "medium", "high", "extreme"]
        risk_index = risk_levels.index(base_risk)

        # Escalate risk based on context
        if defcon <= 2:
            risk_index = min(3, risk_index + 1)

        if world_tension >= 80:
            risk_index = min(3, risk_index + 1)

        if zone:
            stability = getattr(zone, "stability", 50)
            if stability < 30:
                risk_index = min(3, risk_index + 1)

            their_control = getattr(zone, "control_ussr", 50)
            if their_control >= 70:
                risk_index = min(3, risk_index + 1)

        return risk_levels[risk_index]


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

cost_calculator = ActionCostCalculator()
risk_calculator = ActionRiskCalculator()


def calculate_action_cost(
    intention_type: str,
    zone=None,
    defcon: int = 4,
    world_tension: int = 50,
) -> int:
    """Convenience function for calculating action cost."""
    return cost_calculator.calculate(
        intention_type=intention_type,
        zone=zone,
        defcon=defcon,
        world_tension=world_tension,
    )


def calculate_action_cost_breakdown(
    intention_type: str,
    zone=None,
    defcon: int = 4,
    world_tension: int = 50,
) -> dict:
    """Convenience function for getting full cost breakdown."""
    breakdown = cost_calculator.calculate_with_breakdown(
        intention_type=intention_type,
        zone=zone,
        defcon=defcon,
        world_tension=world_tension,
    )
    return breakdown.to_dict()


def calculate_action_risk(
    intention_type: str,
    zone=None,
    defcon: int = 4,
    world_tension: int = 50,
) -> str:
    """Convenience function for calculating action risk."""
    return risk_calculator.calculate(
        intention_type=intention_type,
        zone=zone,
        defcon=defcon,
        world_tension=world_tension,
    )
