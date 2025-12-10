"""Tick processing with Ollama AI for Historia Lite"""
import asyncio
import logging
import random
from typing import List, Optional

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
)
from ai.ollama_ai import OllamaAI, execute_ollama_decision

logger = logging.getLogger(__name__)


async def process_tick_with_ollama(
    world: World,
    event_pool: EventPool,
    ollama: OllamaAI,
    ollama_tiers: List[int] = [1, 2],  # Tiers to use Ollama for
) -> List[Event]:
    """Process one year with Ollama AI for major powers"""
    events: List[Event] = []

    # Set random seed
    random.seed(world.seed + world.year)

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

    # Phase 6: Influence
    events.extend(_process_influence(world))

    # Phase 7: Relations
    _update_relations(world)

    # Advance year
    world.year += 1

    # Store events
    for event in events:
        world.add_event(event)

    logger.info(f"Tick (Ollama) processed: Year {world.year - 1} -> {world.year}")
    return events


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
