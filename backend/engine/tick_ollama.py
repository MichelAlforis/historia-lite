"""Tick processing with Ollama AI for Historia Lite"""
import asyncio
import logging
import random
from typing import List, Optional, Tuple

from .world import World
from .country import Country
from .events import Event, EventPool
from .tick import (
    _process_economy,
    _process_technology,
    _process_conflicts,
    _process_influence,
    _update_relations,
    _apply_event,
    _process_projects,
    _detect_dilemmas,
    _process_blocs,
    _process_summits,
    _process_special_events,
)
from .procedural_events import procedural_generator
from ai.ai_event_generator import ai_event_generator
from .victory import victory_manager, GameEndState
from .nuclear import nuclear_manager
from ai.ollama_ai import OllamaAI, execute_ollama_decision
from ai.decision_tier4 import process_tier4_countries

logger = logging.getLogger(__name__)


async def process_tick_with_ollama(
    world: World,
    event_pool: EventPool,
    ollama: OllamaAI,
    ollama_tiers: List[int] = [1, 2],  # Tiers to use Ollama for
) -> Tuple[List[Event], Optional[GameEndState]]:
    """Process one year with Ollama AI for major powers"""
    events: List[Event] = []

    # Check if game already ended
    if world.game_ended:
        return events, victory_manager.game_end_state

    # Set random seed
    random.seed(world.seed + world.year)

    # Phase 0: Check victory/defeat conditions BEFORE processing
    game_ended, end_state = victory_manager.check_game_end(world)
    if game_ended and end_state:
        world.game_ended = True
        world.game_end_reason = end_state.reason.value if end_state.reason else None
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = end_state.score
        return events, end_state

    # Phase 1: Economy
    events.extend(_process_economy(world))

    # Phase 2: Technology
    events.extend(_process_technology(world))

    # Phase 3: AI Decisions (Ollama for major powers, algorithmic for others)
    ollama_events = await _process_ollama_decisions(world, ollama, ollama_tiers)
    events.extend(ollama_events)

    # Phase 4: Conflicts
    events.extend(_process_conflicts(world))

    # Phase 5: Random Events
    random_events = event_pool.get_random_events(
        world.get_countries_list(), world.year, world.seed
    )
    for event in random_events:
        _apply_event(world, event)
        events.append(event)

    # Phase 5b: Procedural Events
    player_id = None
    player_country = None
    for country in world.countries.values():
        if country.is_player:
            player_id = country.id
            player_country = country
            break
    procedural_events = procedural_generator.generate_events(world, player_id)
    for event in procedural_events:
        _apply_event(world, event)
        events.append(event)
        logger.info(f"Procedural event: {event.title_fr}")

    # Phase 5c: AI Narrative Events (async version for Ollama tick)
    if player_country:
        ai_event = await _generate_ai_narrative_event(world, player_country)
        if ai_event:
            _apply_event(world, ai_event)
            events.append(ai_event)
            logger.info(f"AI narrative event: {ai_event.title_fr}")

    # Phase 6: Influence
    events.extend(_process_influence(world))

    # Phase 7: Relations
    _update_relations(world)

    # Phase 8: Projects
    events.extend(_process_projects(world))

    # Phase 9: Dilemmas
    events.extend(_detect_dilemmas(world))

    # Phase 10: Tier 4 Countries
    tier4_events = process_tier4_countries(world, world.tier4_tick_counter)
    events.extend(tier4_events)
    world.tier4_tick_counter = (world.tier4_tick_counter + 1) % 3

    # Phase 11: Blocs
    events.extend(_process_blocs(world))

    # Phase 12: Summits
    events.extend(_process_summits(world))

    # Phase 13: Special Events
    events.extend(_process_special_events(world))

    # Phase 14: Nuclear DEFCON updates
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

    # Phase 15: Country collapse processing
    collapse_events = victory_manager.process_country_collapse(world)
    events.extend(collapse_events)

    # Check for player defeat after collapse
    game_ended, end_state = victory_manager.check_game_end(world)
    if game_ended and end_state:
        world.game_ended = True
        world.game_end_reason = end_state.reason.value if end_state.reason else None
        world.game_end_message = end_state.message
        world.game_end_message_fr = end_state.message_fr
        world.final_score = end_state.score
        return events, end_state

    # Advance year
    world.year += 1

    # Store events
    for event in events:
        world.add_event(event)

    logger.info(f"Tick (Ollama) processed: Year {world.year - 1} -> {world.year}")
    return events, None


async def _process_ollama_decisions(
    world: World,
    ollama: OllamaAI,
    ollama_tiers: List[int],
) -> List[Event]:
    """Process AI decisions using Ollama for specified tiers"""
    events = []

    # Separate countries by tier
    ollama_countries = []
    algo_countries = []

    for country in world.countries.values():
        if country.is_player:
            continue
        if country.tier in ollama_tiers:
            ollama_countries.append(country)
        else:
            algo_countries.append(country)

    # Process Ollama countries (can be parallelized)
    logger.info(f"Processing {len(ollama_countries)} countries with Ollama...")

    # Process in batches to avoid overwhelming the server
    batch_size = 3
    for i in range(0, len(ollama_countries), batch_size):
        batch = ollama_countries[i:i + batch_size]
        tasks = [_get_ollama_decision(country, world, ollama) for country in batch]
        results = await asyncio.gather(*tasks)

        for country, result in zip(batch, results):
            if result:
                event = execute_ollama_decision(country, world, result)
                if event:
                    events.append(event)
                    logger.info(
                        f"[Ollama] {country.id}: {result.get('action')} - {result.get('reason', '')[:50]}"
                    )
            else:
                # Fallback to algorithmic decision
                from ai.decision import make_decision
                event = make_decision(country, world)
                if event:
                    events.append(event)
                    logger.info(f"[Fallback] {country.id}: algorithmic decision")

    # Process algorithmic countries
    from ai.decision import make_decision
    for country in algo_countries:
        event = make_decision(country, world)
        if event:
            events.append(event)

    return events


async def _get_ollama_decision(
    country: Country, world: World, ollama: OllamaAI
) -> Optional[dict]:
    """Get decision from Ollama for a single country"""
    try:
        return await ollama.make_decision(country, world)
    except Exception as e:
        logger.error(f"Ollama decision failed for {country.id}: {e}")
        return None


async def _generate_ai_narrative_event(
    world: World, player: Country
) -> Optional[Event]:
    """Generate AI narrative event for player (async version)"""
    try:
        # Check cooldown
        if not ai_event_generator._should_generate(player.id, world.year):
            return None

        # Random chance (30%)
        import random
        if random.random() > 0.30:
            return None

        # Generate event
        return await ai_event_generator.generate_narrative_event(
            world=world,
            player=player,
            force=True
        )
    except Exception as e:
        logger.warning(f"AI narrative event generation failed: {e}")
        return None
