"""AI Decision making for Historia Lite"""
import logging
import random
from typing import List, Optional, Tuple

from engine.country import Country
from engine.world import World
from engine.events import Event

logger = logging.getLogger(__name__)


def make_decision(country: Country, world: World) -> Optional[Event]:
    """Main AI decision function for a country"""
    if country.is_player:
        return None

    options = _evaluate_options(country, world)
    if not options:
        return None

    chosen = _weighted_choice(options)
    return _execute_decision(country, world, chosen)


def _evaluate_options(country: Country, world: World) -> List[Tuple[str, float]]:
    """Evaluate all possible options and their scores"""
    options = []

    # Economic development
    if country.economy < 70:
        score = (70 - country.economy) * 0.5
        options.append(("develop_economy", score))

    # Military buildup
    if country.military < 60 or any(
        r in country.rivals for r in world.get_nuclear_powers()
    ):
        base_score = (60 - country.military) * 0.4
        aggression_mult = country.personality.aggression / 50
        options.append(("build_military", base_score * aggression_mult))

    # Stability measures
    if country.stability < 50:
        score = (50 - country.stability) * 0.6
        options.append(("improve_stability", score))

    # Technology investment
    if country.technology < 70 and country.economy > 50:
        score = 25 * (1 - country.technology / 100)
        options.append(("invest_tech", score))

    # Influence expansion (major powers only)
    if country.tier <= 2:
        score = 30 * (country.personality.expansionism / 50)
        options.append(("expand_influence", score))

    # Sanctions on rivals
    for rival_id in country.rivals:
        rival = world.get_country(rival_id)
        if rival and rival_id not in country.sanctions_on:
            score = 15 * (country.personality.aggression / 50)
            options.append((f"sanction_{rival_id}", score))

    # Seek alliance
    if len(country.allies) < 3 and country.personality.diplomacy > 50:
        potential_allies = _find_potential_allies(country, world)
        for ally_id in potential_allies[:2]:
            score = 20 * (country.personality.diplomacy / 50)
            options.append((f"seek_alliance_{ally_id}", score))

    # Nuclear development (if not nuclear and has resources)
    if country.nuclear == 0 and country.technology > 60 and country.tier <= 2:
        if country.personality.risk_tolerance > 60:
            score = 15
            options.append(("nuclear_program", score))

    # Idle (always an option)
    options.append(("idle", 15))

    return options


def _find_potential_allies(country: Country, world: World) -> List[str]:
    """Find countries that could become allies"""
    potential = []
    for other in world.countries.values():
        if other.id == country.id:
            continue
        if other.id in country.allies:
            continue
        if other.id in country.rivals or other.id in country.at_war:
            continue

        # Same bloc preference
        if country.shares_bloc(other):
            potential.append(other.id)
            continue

        # Positive relations
        if country.get_relation(other.id) > 20:
            potential.append(other.id)

    return potential


def _weighted_choice(options: List[Tuple[str, float]]) -> str:
    """Make a weighted random choice from options"""
    if not options:
        return "idle"

    total = sum(score for _, score in options)
    if total <= 0:
        return "idle"

    r = random.random() * total
    cumulative = 0
    for option, score in options:
        cumulative += score
        if r <= cumulative:
            return option

    return options[-1][0]


def _execute_decision(country: Country, world: World, decision: str) -> Optional[Event]:
    """Execute a decision and return the resulting event"""

    if decision == "develop_economy":
        country.economy = min(100, country.economy + 3)
        return _create_event(
            world, country, "decision",
            "Economic Development",
            "Developpement economique",
            f"{country.name} focuses on economic development",
            f"{country.name_fr} se concentre sur le developpement economique"
        )

    elif decision == "build_military":
        country.military = min(100, country.military + 3)
        country.economy = max(0, country.economy - 1)
        return _create_event(
            world, country, "decision",
            "Military Buildup",
            "Renforcement militaire",
            f"{country.name} strengthens its military",
            f"{country.name_fr} renforce son armee"
        )

    elif decision == "improve_stability":
        country.stability = min(100, country.stability + 5)
        return _create_event(
            world, country, "decision",
            "Stability Measures",
            "Mesures de stabilite",
            f"{country.name} implements stability measures",
            f"{country.name_fr} met en place des mesures de stabilite"
        )

    elif decision == "invest_tech":
        country.technology = min(100, country.technology + 3)
        country.economy = max(0, country.economy - 2)
        return _create_event(
            world, country, "decision",
            "Technology Investment",
            "Investissement technologique",
            f"{country.name} invests in technology",
            f"{country.name_fr} investit dans la technologie"
        )

    elif decision == "expand_influence":
        country.soft_power = min(100, country.soft_power + 3)
        return _create_event(
            world, country, "decision",
            "Influence Expansion",
            "Expansion d'influence",
            f"{country.name} expands its global influence",
            f"{country.name_fr} etend son influence mondiale"
        )

    elif decision.startswith("sanction_"):
        target_id = decision.replace("sanction_", "")
        target = world.get_country(target_id)
        if target and target_id not in country.sanctions_on:
            country.sanctions_on.append(target_id)
            country.modify_relation(target_id, -20)
            target.modify_relation(country.id, -20)
            return _create_event(
                world, country, "sanctions",
                "Sanctions Imposed",
                "Sanctions imposees",
                f"{country.name} imposes sanctions on {target.name}",
                f"{country.name_fr} impose des sanctions a {target.name_fr}",
                target_id=target_id
            )

    elif decision.startswith("seek_alliance_"):
        ally_id = decision.replace("seek_alliance_", "")
        ally = world.get_country(ally_id)
        if ally and ally_id not in country.allies:
            # Check if ally accepts (simplified)
            if country.get_relation(ally_id) > 10 or country.shares_bloc(ally):
                country.allies.append(ally_id)
                ally.allies.append(country.id)
                country.modify_relation(ally_id, 15)
                ally.modify_relation(country.id, 15)
                return _create_event(
                    world, country, "diplomacy",
                    "New Alliance",
                    "Nouvelle alliance",
                    f"{country.name} forms an alliance with {ally.name}",
                    f"{country.name_fr} forme une alliance avec {ally.name_fr}",
                    target_id=ally_id
                )

    elif decision == "nuclear_program":
        country.nuclear = min(100, country.nuclear + 5)
        country.soft_power = max(0, country.soft_power - 10)
        # Negative reaction from major powers
        for power in world.get_superpowers():
            if power.id != country.id:
                power.modify_relation(country.id, -15)
        return _create_event(
            world, country, "military",
            "Nuclear Program",
            "Programme nucleaire",
            f"{country.name} advances its nuclear program",
            f"{country.name_fr} fait progresser son programme nucleaire"
        )

    return None


def _create_event(
    world: World,
    country: Country,
    event_type: str,
    title: str,
    title_fr: str,
    description: str,
    description_fr: str,
    target_id: Optional[str] = None
) -> Event:
    """Create an event"""
    return Event(
        id=f"decision_{world.year}_{country.id}_{event_type}",
        year=world.year,
        type=event_type,
        title=title,
        title_fr=title_fr,
        description=description,
        description_fr=description_fr,
        country_id=country.id,
        target_id=target_id,
    )
