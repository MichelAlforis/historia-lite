"""Simplified AI decision logic for Tier 4 countries"""
import random
import logging
from typing import TYPE_CHECKING, List, Optional

from engine.country import Tier4Country
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World

logger = logging.getLogger(__name__)


# Tier 4 actions
ACTION_DEVELOP = "develop"
ACTION_SHIFT_ALIGNMENT = "shift_alignment"
ACTION_CRISIS = "crisis"


def decide_tier4_action(
    country: Tier4Country,
    world: "World"
) -> tuple[str, dict]:
    """
    Decide action for a Tier 4 country.
    Returns (action_type, action_params).

    Actions:
    - DEVELOP: +2 economy (with potential help from influential power)
    - SHIFT_ALIGNMENT: Pivot towards another power (+/-20 alignment)
    - CRISIS: If stability < 30, risk of coup/unrest
    """
    # Check for crisis first (high priority if stability is very low)
    if country.stability < 30:
        crisis_chance = (30 - country.stability) / 100 + 0.1  # 10-40% chance
        if random.random() < crisis_chance:
            return ACTION_CRISIS, _generate_crisis(country)

    # Decide between develop and shift alignment
    # Countries with low economy tend to develop
    # Countries with strong alignment pressure tend to shift

    develop_weight = 60  # Base weight for development
    shift_weight = 40    # Base weight for alignment shift

    # Adjust weights based on country state
    if country.economy < 20:
        develop_weight += 30  # Poor countries focus on development
    elif country.economy > 35:
        shift_weight += 20    # Richer countries play politics

    # Check for influence pressure from major powers
    influence_pressure = _calculate_influence_pressure(country, world)
    if abs(influence_pressure) > 30:
        shift_weight += 25    # Strong pressure encourages alignment shift

    # Random decision weighted by factors
    total = develop_weight + shift_weight
    if random.randint(1, total) <= develop_weight:
        return ACTION_DEVELOP, _develop_action(country, world)
    else:
        return ACTION_SHIFT_ALIGNMENT, _shift_alignment_action(country, world)


def _calculate_influence_pressure(country: Tier4Country, world: "World") -> int:
    """
    Calculate net influence pressure on a Tier 4 country.
    Negative = West pressure, Positive = East pressure.
    """
    pressure = 0

    # Check relations with major powers
    usa_relation = country.get_relation("USA")
    chn_relation = country.get_relation("CHN")
    rus_relation = country.get_relation("RUS")

    # West pressure from USA
    if usa_relation > 20:
        pressure -= 20
    elif usa_relation < -20:
        pressure += 10

    # East pressure from China
    if chn_relation > 20:
        pressure += 20
    elif chn_relation < -20:
        pressure -= 10

    # East pressure from Russia
    if rus_relation > 20:
        pressure += 15
    elif rus_relation < -20:
        pressure -= 5

    return pressure


def _develop_action(country: Tier4Country, world: "World") -> dict:
    """Generate development action parameters"""
    # Determine which power might help
    helping_power = None
    help_bonus = 0

    # Pro-West countries get help from USA/EU
    if country.alignment < -30:
        helping_power = "USA" if random.random() < 0.6 else "EU"
        help_bonus = 1
    # Pro-East countries get help from China/Russia
    elif country.alignment > 30:
        helping_power = "CHN" if random.random() < 0.7 else "RUS"
        help_bonus = 1

    return {
        "economy_boost": 2 + help_bonus,
        "stability_boost": 1 if country.stability < 50 else 0,
        "helping_power": helping_power
    }


def _shift_alignment_action(country: Tier4Country, world: "World") -> dict:
    """Generate alignment shift action parameters"""
    # Determine shift direction based on various factors
    shift = 0
    target = country.alignment_target
    new_target = target

    # Countries tend to shift towards better economic partners
    usa_economy = world.countries.get("USA")
    chn_economy = world.countries.get("CHN")

    if usa_economy and chn_economy:
        # China's economic growth creates eastward pull
        if chn_economy.economy > usa_economy.economy - 10:
            shift += 10

    # Regional influence matters
    regional_pull = _calculate_regional_pull(country, world)
    shift += regional_pull

    # Current alignment affects shift (regression towards mean)
    if country.alignment > 50:
        shift -= random.randint(5, 15)  # Very pro-East might moderate
    elif country.alignment < -50:
        shift += random.randint(5, 15)  # Very pro-West might moderate
    else:
        # Neutral countries pick a side based on neighbors and benefits
        shift += random.randint(-15, 15)

    # Determine new target if significant shift
    if country.alignment + shift > 40:
        new_target = "CHN" if random.random() < 0.6 else "RUS"
    elif country.alignment + shift < -40:
        new_target = "USA" if random.random() < 0.5 else "EU"
    elif abs(country.alignment + shift) < 20:
        new_target = "NONE"

    return {
        "alignment_shift": max(-20, min(20, shift)),
        "new_target": new_target,
        "reason": _get_shift_reason(shift)
    }


def _calculate_regional_pull(country: Tier4Country, world: "World") -> int:
    """Calculate regional alignment pull based on neighbors"""
    if not country.neighbors:
        return 0

    total_alignment = 0
    count = 0

    for neighbor_id in country.neighbors:
        # Check in tier4 countries
        neighbor = world.tier4_countries.get(neighbor_id)
        if neighbor:
            total_alignment += neighbor.alignment
            count += 1
        else:
            # Check in main countries
            main_country = world.countries.get(neighbor_id)
            if main_country:
                # Major powers have strong pull
                if neighbor_id == "USA":
                    total_alignment -= 50
                elif neighbor_id in ("CHN", "RUS"):
                    total_alignment += 50
                elif neighbor_id in main_country.blocs:
                    if "NATO" in main_country.blocs or "EU" in main_country.blocs:
                        total_alignment -= 20
                    elif "BRICS" in main_country.blocs:
                        total_alignment += 20
                count += 1

    if count == 0:
        return 0

    avg_alignment = total_alignment / count
    # Regional pull is partial influence from average neighbor alignment
    return int((avg_alignment - country.alignment) * 0.15)


def _get_shift_reason(shift: int) -> str:
    """Get human-readable reason for alignment shift"""
    if shift > 10:
        return "economic_partnership_east"
    elif shift > 0:
        return "regional_influence"
    elif shift < -10:
        return "western_investment"
    elif shift < 0:
        return "democratic_values"
    else:
        return "status_quo"


def _generate_crisis(country: Tier4Country) -> dict:
    """Generate crisis parameters for unstable country"""
    crisis_types = [
        ("coup", 40),
        ("civil_unrest", 35),
        ("economic_collapse", 25)
    ]

    # Weight by country characteristics
    weights = []
    for crisis_type, base_weight in crisis_types:
        weight = base_weight
        if crisis_type == "coup" and country.military > 20:
            weight += 15  # Strong military = higher coup risk
        elif crisis_type == "economic_collapse" and country.economy < 15:
            weight += 20  # Poor economy = higher collapse risk
        elif crisis_type == "civil_unrest":
            weight += 10  # Always possible
        weights.append((crisis_type, weight))

    # Select crisis type
    total = sum(w for _, w in weights)
    roll = random.randint(1, total)
    cumulative = 0
    selected_crisis = "civil_unrest"
    for crisis_type, weight in weights:
        cumulative += weight
        if roll <= cumulative:
            selected_crisis = crisis_type
            break

    # Generate crisis effects
    effects = {
        "coup": {
            "stability_loss": -25,
            "economy_loss": -10,
            "alignment_flip": random.choice([True, False]),
            "description_fr": "Coup d'etat militaire"
        },
        "civil_unrest": {
            "stability_loss": -15,
            "economy_loss": -5,
            "alignment_flip": False,
            "description_fr": "Troubles civils"
        },
        "economic_collapse": {
            "stability_loss": -10,
            "economy_loss": -20,
            "alignment_flip": False,
            "description_fr": "Effondrement economique"
        }
    }

    return {
        "crisis_type": selected_crisis,
        **effects[selected_crisis]
    }


def apply_tier4_action(
    country: Tier4Country,
    action: str,
    params: dict,
    world: "World"
) -> Optional[Event]:
    """
    Apply a Tier 4 action to the country and return event if notable.
    """
    event = None

    if action == ACTION_DEVELOP:
        # Apply development
        country.economy = min(100, country.economy + params.get("economy_boost", 2))
        country.stability = min(100, country.stability + params.get("stability_boost", 0))

        helping_power = params.get("helping_power")
        if helping_power:
            country.modify_relation(helping_power, 5)
            # Slight alignment shift towards helper
            if helping_power in ("USA", "EU"):
                country.shift_alignment(-5)
            elif helping_power in ("CHN", "RUS"):
                country.shift_alignment(5)

            event = Event(
                id=f"tier4_dev_{world.year}_{country.id}",
                year=world.year,
                type="tier4_development",
                title="Development Aid",
                title_fr="Aide au developpement",
                description=f"{country.name} receives development aid from {helping_power}",
                description_fr=f"{country.name_fr} recoit une aide au developpement de {helping_power}",
                country_id=country.id,
                target_id=helping_power
            )

    elif action == ACTION_SHIFT_ALIGNMENT:
        # Apply alignment shift
        old_alignment = country.alignment
        country.shift_alignment(params.get("alignment_shift", 0))
        country.alignment_target = params.get("new_target", country.alignment_target)

        # Significant shifts generate events
        if abs(params.get("alignment_shift", 0)) >= 15:
            direction = "East" if params.get("alignment_shift", 0) > 0 else "West"
            direction_fr = "l'Est" if params.get("alignment_shift", 0) > 0 else "l'Ouest"
            event = Event(
                id=f"tier4_align_{world.year}_{country.id}",
                year=world.year,
                type="tier4_alignment",
                title=f"Geopolitical Pivot",
                title_fr=f"Pivot geopolitique",
                description=f"{country.name} pivots towards the {direction}",
                description_fr=f"{country.name_fr} se tourne vers {direction_fr}",
                country_id=country.id
            )

    elif action == ACTION_CRISIS:
        # Apply crisis effects
        country.stability = max(0, country.stability + params.get("stability_loss", -15))
        country.economy = max(0, country.economy + params.get("economy_loss", -5))
        country.in_crisis = True
        country.crisis_type = params.get("crisis_type")

        # Alignment flip on coup
        if params.get("alignment_flip"):
            country.alignment = -country.alignment
            if country.alignment > 30:
                country.alignment_target = "CHN" if random.random() < 0.6 else "RUS"
            elif country.alignment < -30:
                country.alignment_target = "USA" if random.random() < 0.5 else "EU"
            else:
                country.alignment_target = "NONE"

        crisis_title = {
            "coup": "Coup d'etat",
            "civil_unrest": "Civil Unrest",
            "economic_collapse": "Economic Collapse"
        }.get(params.get("crisis_type", "unrest"), "Crisis")

        event = Event(
            id=f"tier4_crisis_{world.year}_{country.id}",
            year=world.year,
            type="tier4_crisis",
            title=crisis_title,
            title_fr=params.get("description_fr", "Crise"),
            description=f"Crisis in {country.name}: {params.get('crisis_type', 'unrest').replace('_', ' ')}",
            description_fr=f"Crise en {country.name_fr}: {params.get('description_fr', 'troubles')}",
            country_id=country.id
        )

        logger.info(f"Crisis in {country.id}: {params.get('crisis_type')}")

    return event


def process_tier4_countries(
    world: "World",
    tick_counter: int
) -> List[Event]:
    """
    Process all Tier 4 countries.
    Only processes every 3 ticks to reduce computation.

    Args:
        world: The world state
        tick_counter: Current tick count (0, 1, 2, 0, 1, 2, ...)

    Returns:
        List of events generated
    """
    events = []

    # Only process on tick_counter == 0 (every 3 ticks)
    if tick_counter % 3 != 0:
        return events

    for country_id, country in world.tier4_countries.items():
        # Decide and apply action
        action, params = decide_tier4_action(country, world)
        event = apply_tier4_action(country, action, params, world)

        if event:
            events.append(event)

        # Recovery from crisis
        if country.in_crisis:
            # 30% chance to recover each processed tick
            if random.random() < 0.3:
                country.in_crisis = False
                country.crisis_type = None
                country.stability = min(100, country.stability + 5)

    logger.info(f"Processed {len(world.tier4_countries)} Tier 4 countries, {len(events)} events")
    return events
