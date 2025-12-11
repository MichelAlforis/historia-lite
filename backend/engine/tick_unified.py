"""Unified tick processing for Historia Lite - Phase 13

Uses UnifiedWorld and BaseCountry with dynamic tier management.
Countries are processed based on their tier-specific frequency.
"""
import logging
import random
from typing import List, Tuple, Optional

from .world_unified import UnifiedWorld
from .base_country import BaseCountry
from .tier_manager import TierManager
from .events import Event, EventPool
from .victory import victory_manager, GameEndState
from .nuclear import nuclear_manager

logger = logging.getLogger(__name__)


def process_unified_tick(
    world: UnifiedWorld,
    event_pool: EventPool
) -> Tuple[List[Event], Optional[GameEndState]]:
    """
    Process one year of simulation using unified architecture.

    Key differences from legacy tick:
    - All countries in single dict
    - Processing frequency based on BaseCountry.process_frequency
    - Dynamic tier changes via TierManager

    Returns (events, game_end_state) - game_end_state is None if game continues.
    """
    events: List[Event] = []

    # Check if game already ended
    if world.game_ended:
        return events, None

    # Set random seed for reproducibility
    random.seed(world.seed + world.year)

    # Phase 0: Check victory/defeat conditions BEFORE processing
    game_ended, end_state = _check_game_end_unified(world)
    if game_ended and end_state:
        world.game_ended = True
        world.game_end_reason = end_state.reason.value if end_state.reason else None
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = end_state.score
        return events, end_state

    # Phase 1: Process countries by tier frequency
    countries_to_process = world.get_countries_to_process()
    logger.debug(f"Processing {len(countries_to_process)} countries this tick (tick #{world.tick_counter})")

    # Phase 1a: Economy for processed countries
    for country in countries_to_process:
        econ_events = _process_country_economy(country, world)
        events.extend(econ_events)

    # Phase 1b: Stability updates
    for country in countries_to_process:
        stability_events = _process_country_stability(country, world)
        events.extend(stability_events)

    # Phase 1c: AI decisions based on tier
    for country in countries_to_process:
        ai_events = _process_country_ai(country, world)
        events.extend(ai_events)

    # Phase 2: Global events (affect all, not tier-limited)
    random_events = _get_random_events_unified(world, event_pool)
    for event in random_events:
        _apply_event_unified(world, event)
        events.append(event)

    # Phase 3: Relations updates (major powers only)
    _update_relations_unified(world)

    # Phase 4: Conflict processing
    conflict_events = _process_conflicts_unified(world)
    events.extend(conflict_events)

    # Phase 5: Nuclear DEFCON updates
    nuclear_events = nuclear_manager.update_defcon(world)
    events.extend(nuclear_events)

    # Check for nuclear war game end
    if world.defcon_level == 0:
        end_state = GameEndState(
            is_victory=False,
            reason=None,
            message="Nuclear war has devastated the world.",
            message_fr="Une guerre nucleaire a devaste le monde.",
            score=0
        )
        world.game_ended = True
        world.game_end_reason = "nuclear_annihilation"
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = 0
        return events, end_state

    # Phase 6: Tier changes (every 5 ticks)
    if world.tick_counter % 5 == 0:
        tier_changes = world.process_tier_changes()
        for change in tier_changes:
            event = Event(
                id=f"tier_change_{world.year}_{change['country_id']}",
                type="tier_change",
                title=f"{change['country_id']} tier change: {change['old_tier']} -> {change['new_tier']}",
                title_fr=f"Changement de rang: {change['country_id']} passe du tier {change['old_tier']} au tier {change['new_tier']}",
                description=f"Based on power score and stability",
                description_fr=f"Base sur le score de puissance et la stabilite",
                year=world.year,
                countries=[change['country_id']],
                severity=2 if change['new_tier'] < change['old_tier'] else -2,
            )
            events.append(event)
            logger.info(f"Tier change: {change['country_id']} {change['old_tier']} -> {change['new_tier']}")

    # Phase 7: Check game end after processing
    game_ended, end_state = _check_game_end_unified(world)
    if game_ended and end_state:
        world.game_ended = True
        world.game_end_reason = end_state.reason.value if end_state.reason else None
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = end_state.score
        return events, end_state

    # Increment counters
    world.tick_counter = (world.tick_counter + 1) % 30  # LCM of process frequencies
    world.year += 1

    # Store events in history
    for event in events:
        world.add_event(event)

    logger.info(f"Tick {world.tick_counter} complete. Year {world.year}. {len(events)} events.")
    return events, None


def _process_country_economy(country: BaseCountry, world: UnifiedWorld) -> List[Event]:
    """Process economic changes for a single country"""
    events = []

    # Base economic growth depends on stability and tier
    base_growth = 1 if country.stability > 50 else -1
    tier_bonus = max(0, 4 - country.tier)  # Higher tiers grow faster

    # Apply growth
    old_economy = country.economy
    country.economy = max(0, min(100, country.economy + base_growth + tier_bonus // 2))

    # Significant change event
    if abs(country.economy - old_economy) >= 5:
        direction = "growth" if country.economy > old_economy else "decline"
        events.append(Event(
            id=f"econ_{world.year}_{country.id}",
            type="economy",
            title=f"Economic {direction} in {country.name}",
            title_fr=f"{'Croissance' if direction == 'growth' else 'Declin'} economique: {country.name_fr}",
            description=f"Economy changed from {old_economy} to {country.economy}",
            description_fr=f"Economie: {old_economy} -> {country.economy}",
            year=world.year,
            countries=[country.id],
            severity=1 if direction == "growth" else -1,
        ))

    return events


def _process_country_stability(country: BaseCountry, world: UnifiedWorld) -> List[Event]:
    """Process stability changes for a single country"""
    events = []

    # Stability affected by economy and conflicts
    if country.economy < 30:
        country.stability = max(0, country.stability - 2)
    elif country.economy > 70:
        country.stability = min(100, country.stability + 1)

    # At war = stability loss
    if country.at_war:
        country.stability = max(0, country.stability - 3)

    # Crisis event if stability critically low
    if country.stability < 20 and random.random() < 0.3:
        events.append(Event(
            id=f"crisis_{world.year}_{country.id}",
            type="crisis",
            title=f"Political crisis in {country.name}",
            title_fr=f"Crise politique: {country.name_fr}",
            description=f"Stability at critical level: {country.stability}",
            description_fr=f"Stabilite critique: {country.stability}",
            year=world.year,
            countries=[country.id],
            severity=-3,
        ))

    return events


def _process_country_ai(country: BaseCountry, world: UnifiedWorld) -> List[Event]:
    """Process AI decisions based on country tier"""
    events = []

    # AI level determines decision complexity
    ai_level = country.ai_level

    if ai_level == "passive":
        # Tier 6: No autonomous decisions, follow protector
        if country.protector:
            protector = world.get_country(country.protector)
            if protector:
                # Align with protector
                if country.alignment is not None and protector.alignment is not None:
                    country.alignment = int(country.alignment * 0.9 + protector.alignment * 0.1)

    elif ai_level == "minimal":
        # Tier 5: Regional tendency only
        if random.random() < 0.1:  # 10% chance of alignment shift
            regional_trend = _calculate_regional_trend(country, world)
            if country.alignment is not None:
                country.alignment = max(-100, min(100, country.alignment + regional_trend))

    elif ai_level == "simplified":
        # Tier 4: Basic decisions
        if random.random() < 0.2:  # 20% chance of action
            # Could improve relations or shift alignment
            if country.alignment is not None:
                pressure = _calculate_alignment_pressure(country, world)
                if abs(pressure) > 20:
                    country.alignment = max(-100, min(100, country.alignment + pressure // 5))

    elif ai_level in ("standard", "full"):
        # Tier 1-3: Full AI (handled by existing decision modules)
        # These would call the existing ai.decision module
        pass

    return events


def _calculate_regional_trend(country: BaseCountry, world: UnifiedWorld) -> int:
    """Calculate regional alignment trend"""
    neighbors = [world.get_country(n) for n in (country.neighbors or [])]
    neighbors = [n for n in neighbors if n and n.alignment is not None]

    if not neighbors:
        return 0

    avg_alignment = sum(n.alignment for n in neighbors) / len(neighbors)
    return int((avg_alignment - (country.alignment or 0)) * 0.1)


def _calculate_alignment_pressure(country: BaseCountry, world: UnifiedWorld) -> int:
    """Calculate pressure from major powers on alignment"""
    pressure = 0

    # USA influence (negative alignment = pro-West)
    usa = world.get_country("USA")
    if usa:
        relation = country.relations.get("USA", 0)
        if relation > 30:
            pressure -= 10
        elif relation < -30:
            pressure += 5

    # China influence (positive alignment = pro-East)
    chn = world.get_country("CHN")
    if chn:
        relation = country.relations.get("CHN", 0)
        if relation > 30:
            pressure += 10
        elif relation < -30:
            pressure -= 5

    return pressure


def _get_random_events_unified(world: UnifiedWorld, event_pool: EventPool) -> List[Event]:
    """Get random events appropriate for unified world"""
    countries_list = world.get_countries_list()
    return event_pool.get_random_events(countries_list, world.year, world.seed)


def _apply_event_unified(world: UnifiedWorld, event: Event) -> None:
    """Apply event effects to unified world"""
    for country_id in event.countries:
        country = world.get_country(country_id)
        if not country:
            continue

        # Apply effects based on event type
        if event.type == "economy":
            country.economy = max(0, min(100, country.economy + event.severity * 2))
        elif event.type == "stability":
            country.stability = max(0, min(100, country.stability + event.severity * 2))
        elif event.type == "military":
            if country.military is not None:
                country.military = max(0, min(100, country.military + event.severity * 2))


def _update_relations_unified(world: UnifiedWorld) -> None:
    """Update diplomatic relations between major powers"""
    major_powers = world.get_major_powers()

    for country in major_powers:
        for other in major_powers:
            if country.id == other.id:
                continue

            current = country.relations.get(other.id, 0)

            # Drift towards 0 over time (normalization)
            if current > 0:
                country.relations[other.id] = current - 1
            elif current < 0:
                country.relations[other.id] = current + 1

            # Shared enemies improve relations
            shared_enemies = set(country.at_war) & set(other.at_war)
            if shared_enemies:
                country.relations[other.id] = min(100, current + 5)


def _process_conflicts_unified(world: UnifiedWorld) -> List[Event]:
    """Process active conflicts in unified world"""
    events = []

    for conflict in world.active_conflicts:
        conflict.duration += 1

        # Conflict fatigue after 3 years
        if conflict.duration > 3:
            # Chance of peace
            if random.random() < 0.2:
                world.end_conflict(conflict.id)
                events.append(Event(
                    id=f"peace_{world.year}_{conflict.id}",
                    type="peace",
                    title=f"Peace achieved: {conflict.id}",
                    title_fr=f"Paix conclue: {conflict.id}",
                    description="Conflict ended due to war fatigue",
                    description_fr="Conflit termine par lassitude",
                    year=world.year,
                    countries=conflict.attackers + conflict.defenders,
                    severity=2,
                ))

        # Nuclear escalation risk
        if conflict.nuclear_risk > 0:
            conflict.nuclear_risk = min(100, conflict.nuclear_risk + 2)
            if conflict.nuclear_risk > 80 and random.random() < 0.1:
                world.defcon_level = max(1, world.defcon_level - 1)

    return events


def _check_game_end_unified(world: UnifiedWorld) -> Tuple[bool, Optional[GameEndState]]:
    """Check for game end conditions in unified world"""
    # Player country collapse
    if world.player_country_id:
        player = world.get_country(world.player_country_id)
        if player:
            if player.stability <= 0:
                return True, GameEndState(
                    is_victory=False,
                    reason=None,
                    message=f"{player.name} has collapsed due to instability.",
                    message_fr=f"{player.name_fr} s'est effondre par instabilite.",
                    score=0
                )

    # Scenario end year
    if world.scenario_end_year and world.year >= world.scenario_end_year:
        score = _calculate_final_score(world)
        return True, GameEndState(
            is_victory=score > 50,
            reason=None,
            message=f"Scenario completed. Final score: {score}",
            message_fr=f"Scenario termine. Score final: {score}",
            score=score
        )

    return False, None


def _calculate_final_score(world: UnifiedWorld) -> int:
    """Calculate final score for unified world"""
    if not world.player_country_id:
        return 50

    player = world.get_country(world.player_country_id)
    if not player:
        return 0

    score = player.power_score

    # Bonus for allies
    allies_bonus = len([c for c in world.countries.values()
                        if c.relations.get(player.id, 0) > 50]) * 2

    # Penalty for wars
    war_penalty = len(player.at_war) * 5

    return max(0, min(100, score + allies_bonus - war_penalty))
