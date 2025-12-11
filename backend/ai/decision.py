"""AI Decision making for Historia Lite - Stochastic AI with memory"""
import logging
import random
from typing import List, Optional, Tuple, Dict
from collections import defaultdict

from engine.country import Country
from engine.world import World
from engine.events import Event

logger = logging.getLogger(__name__)

# ============================================================================
# STOCHASTIC AI SYSTEM
# Adds variance, grudges, moods, and strategic memory
# ============================================================================

# Global AI memory - persists grudges and past events
_ai_memory: Dict[str, Dict] = defaultdict(lambda: {
    "grudges": {},        # country_id -> offense_level (0-100)
    "mood": 50,           # 0=aggressive, 100=peaceful, 50=neutral
    "strategic_focus": None,  # Current priority
    "last_action": None,
    "consecutive_same": 0,  # Avoid repetition
})

# Stochastic variance range (percentage)
VARIANCE_RANGE = 0.3  # +/- 30% variance on scores


def _apply_variance(score: float) -> float:
    """Apply stochastic variance to a score"""
    variance = random.uniform(1 - VARIANCE_RANGE, 1 + VARIANCE_RANGE)
    return score * variance


def _get_country_mood(country: Country) -> int:
    """Calculate current mood based on situation"""
    memory = _ai_memory[country.id]

    # Base mood from personality
    base_mood = 100 - country.personality.aggression

    # Modify by recent events
    if country.at_war:
        base_mood -= 30  # Wars make countries aggressive

    if country.stability < 40:
        base_mood -= 20  # Instability creates tension

    if country.economy > 70:
        base_mood += 10  # Prosperity calms

    # Add random daily fluctuation (-10 to +10)
    fluctuation = random.randint(-10, 10)

    # Update and constrain mood
    memory["mood"] = max(0, min(100, base_mood + fluctuation))
    return memory["mood"]


def _record_grudge(country_id: str, offender_id: str, offense_level: int) -> None:
    """Record a grudge against another country"""
    memory = _ai_memory[country_id]
    current = memory["grudges"].get(offender_id, 0)
    # Grudges accumulate but decay slowly
    memory["grudges"][offender_id] = min(100, current + offense_level)


def _decay_grudges(country_id: str) -> None:
    """Decay grudges over time"""
    memory = _ai_memory[country_id]
    for offender_id in list(memory["grudges"].keys()):
        memory["grudges"][offender_id] = max(0, memory["grudges"][offender_id] - 5)
        if memory["grudges"][offender_id] <= 0:
            del memory["grudges"][offender_id]


def _get_grudge_targets(country: Country) -> List[Tuple[str, int]]:
    """Get countries this AI has grudges against"""
    memory = _ai_memory[country.id]
    return [(k, v) for k, v in memory["grudges"].items() if v > 20]


def make_decision(country: Country, world: World) -> Optional[Event]:
    """Main AI decision function for a country with stochastic elements"""
    if country.is_player:
        return None

    # Decay grudges each turn
    _decay_grudges(country.id)

    # Get current mood
    mood = _get_country_mood(country)

    options = _evaluate_options(country, world, mood)
    if not options:
        return None

    # Apply variance to all scores
    options_with_variance = [(opt, _apply_variance(score)) for opt, score in options]

    # Check for repetition avoidance
    memory = _ai_memory[country.id]
    chosen = _weighted_choice(options_with_variance)

    # Avoid doing the same thing 3 times in a row
    if chosen == memory["last_action"]:
        memory["consecutive_same"] += 1
        if memory["consecutive_same"] >= 3:
            # Force different action
            other_options = [(o, s) for o, s in options_with_variance if o != chosen]
            if other_options:
                chosen = _weighted_choice(other_options)
                memory["consecutive_same"] = 0
    else:
        memory["last_action"] = chosen
        memory["consecutive_same"] = 0

    return _execute_decision(country, world, chosen)


def _evaluate_options(country: Country, world: World, mood: int = 50) -> List[Tuple[str, float]]:
    """Evaluate all possible options and their scores with mood influence"""
    options = []

    # Mood modifiers
    aggressive_mult = 1.5 if mood < 30 else (0.7 if mood > 70 else 1.0)
    peaceful_mult = 1.5 if mood > 70 else (0.7 if mood < 30 else 1.0)

    # Economic development
    if country.economy < 70:
        score = (70 - country.economy) * 0.5 * peaceful_mult
        options.append(("develop_economy", score))

    # Military buildup - boosted when aggressive or threatened
    threat_level = _assess_threats(country, world)
    if country.military < 60 or threat_level > 30:
        base_score = (60 - country.military) * 0.4 + threat_level * 0.3
        aggression_mult = country.personality.aggression / 50 * aggressive_mult
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
        score = 30 * (country.personality.expansionism / 50) * aggressive_mult
        options.append(("expand_influence", score))

    # Sanctions on rivals (boosted by grudges)
    for rival_id in country.rivals:
        rival = world.get_country(rival_id)
        if rival and rival_id not in country.sanctions_on:
            grudge = _ai_memory[country.id]["grudges"].get(rival_id, 0)
            score = (15 + grudge * 0.3) * (country.personality.aggression / 50) * aggressive_mult
            options.append((f"sanction_{rival_id}", score))

    # Grudge-based retaliation (sanctions on non-rivals who offended)
    grudge_targets = _get_grudge_targets(country)
    for target_id, grudge_level in grudge_targets:
        if target_id not in country.rivals and target_id not in country.sanctions_on:
            target = world.get_country(target_id)
            if target:
                score = grudge_level * 0.3 * aggressive_mult
                options.append((f"sanction_{target_id}", score))

    # Seek alliance - boosted when peaceful or threatened
    if len(country.allies) < 3:
        potential_allies = _find_potential_allies(country, world)
        for ally_id in potential_allies[:2]:
            score = 20 * (country.personality.diplomacy / 50) * peaceful_mult
            # Boost if we share an enemy
            ally = world.get_country(ally_id)
            if ally and any(r in ally.rivals for r in country.rivals):
                score *= 1.5  # Enemy of my enemy
            options.append((f"seek_alliance_{ally_id}", score))

    # Nuclear development (if not nuclear and has resources)
    if country.nuclear == 0 and country.technology > 60 and country.tier <= 2:
        # More likely if threatened by nuclear power
        nuclear_threat = any(
            world.get_country(r) and world.get_country(r).nuclear > 0
            for r in country.rivals
        )
        base_score = 15
        if nuclear_threat:
            base_score = 35

        if country.personality.risk_tolerance > 60 or nuclear_threat:
            options.append(("nuclear_program", base_score * aggressive_mult))

    # Reconciliation option (reduce tensions with non-allies when peaceful)
    if mood > 60:
        for other_id, relation in list(country.relations.items())[:5]:
            if relation < -20 and other_id not in country.at_war:
                other = world.get_country(other_id)
                if other and other_id not in country.rivals:
                    score = 15 * peaceful_mult
                    options.append((f"reconcile_{other_id}", score))

    # Idle (always an option) - more likely when content
    idle_score = 15
    if country.economy > 70 and country.stability > 70 and country.military > 50:
        idle_score = 30  # Content countries do less
    options.append(("idle", idle_score))

    return options


def _assess_threats(country: Country, world: World) -> int:
    """Assess threat level from rivals and enemies"""
    threat = 0

    # Direct wars
    for enemy_id in country.at_war:
        enemy = world.get_country(enemy_id)
        if enemy:
            threat += 30 + (enemy.military - country.military) // 2

    # Rival military buildup
    for rival_id in country.rivals:
        rival = world.get_country(rival_id)
        if rival and rival.military > country.military:
            threat += (rival.military - country.military) // 3

    # Nuclear threats
    for rival_id in country.rivals:
        rival = world.get_country(rival_id)
        if rival and rival.nuclear > 0 and country.nuclear == 0:
            threat += 25

    return min(100, threat)


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
            # Record grudge for the target (they will remember this offense)
            _record_grudge(target_id, country.id, 30)
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

    elif decision.startswith("reconcile_"):
        target_id = decision.replace("reconcile_", "")
        target = world.get_country(target_id)
        if target:
            # Improve relations both ways
            country.modify_relation(target_id, 15)
            target.modify_relation(country.id, 10)
            # Reduce grudges
            memory = _ai_memory[country.id]
            if target_id in memory["grudges"]:
                memory["grudges"][target_id] = max(0, memory["grudges"][target_id] - 20)
            # Also reduce target's grudge against us
            target_memory = _ai_memory[target_id]
            if country.id in target_memory["grudges"]:
                target_memory["grudges"][country.id] = max(0, target_memory["grudges"][country.id] - 15)
            # Remove sanctions if any
            if target_id in country.sanctions_on:
                country.sanctions_on.remove(target_id)
            return _create_event(
                world, country, "diplomacy",
                "Reconciliation Effort",
                "Effort de reconciliation",
                f"{country.name} seeks to improve relations with {target.name}",
                f"{country.name_fr} cherche a ameliorer ses relations avec {target.name_fr}",
                target_id=target_id
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
