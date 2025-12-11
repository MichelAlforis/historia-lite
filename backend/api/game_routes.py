"""Core game routes for Historia Lite - state, tick, reset, countries"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.tick import process_tick, process_tick_legacy
from engine.tick_unified import process_unified_tick
from engine.world_unified import UnifiedWorld
from engine.world import GameDate
from schemas.game import (
    WorldStateResponse,
    CountryResponse,
    InfluenceZoneResponse,
    EventResponse,
    ConflictResponse,
    TickResponse,
)
from api.game_state import (
    get_world,
    get_event_pool,
    get_timeline,
    reset_world,
    is_unified_mode,
    set_unified_mode,
)

logger = logging.getLogger(__name__)


# Additional response models for timeline integration
class TimelineEventBrief(BaseModel):
    id: str
    date: str
    actor_country: str
    title_fr: str
    type: str
    importance: int


class MonthlyTickResponse(BaseModel):
    """Response for monthly tick with timeline events"""
    year: int
    month: int
    date_display: str
    date_display_fr: str
    events: List[EventResponse]
    timeline_events: List[TimelineEventBrief]
    summary: str
    summary_fr: str
    game_ended: bool
    game_end_reason: Optional[str] = None
    game_end_message: Optional[str] = None
    game_end_message_fr: Optional[str] = None
    is_victory: bool = False
    final_score: Optional[int] = None
    defcon_level: int
    unread_events: int

router = APIRouter(prefix="/api", tags=["game"])


@router.get("/state", response_model=WorldStateResponse)
async def get_state():
    """Get the current world state with timeline info"""
    world = get_world()
    timeline = get_timeline()

    countries = [CountryResponse.from_country(c) for c in world.countries.values()]
    zones = [InfluenceZoneResponse.from_zone(z) for z in world.influence_zones.values()]
    conflicts = [
        ConflictResponse(
            id=c.id,
            type=c.type,
            attackers=c.attackers,
            defenders=c.defenders,
            region=c.region,
            intensity=c.intensity,
            duration=c.duration,
            nuclear_risk=c.nuclear_risk,
        )
        for c in world.active_conflicts
    ]
    recent_events = [EventResponse.from_event(e) for e in world.get_recent_events(30)]

    tier4_in_crisis = len([c for c in world.tier4_countries.values() if c.in_crisis])
    tier5_in_crisis = len([c for c in world.tier5_countries.values() if c.in_crisis])

    return WorldStateResponse(
        year=world.year,
        month=world.month,  # NEW: month field
        date_display=world.date_display,  # NEW: "Janvier 2025"
        seed=world.seed,
        oil_price=world.oil_price,
        global_tension=world.global_tension,
        countries=countries,
        influence_zones=zones,
        active_conflicts=conflicts,
        recent_events=recent_events,
        total_countries=world.get_all_countries_count(),
        nuclear_powers=len(world.get_nuclear_powers()),
        active_wars=len(world.active_conflicts),
        tier4_count=len(world.tier4_countries),
        tier4_in_crisis=tier4_in_crisis,
        tier5_count=len(world.tier5_countries),
        tier5_in_crisis=tier5_in_crisis,
        tier6_count=len(world.tier6_countries),
        defcon_level=world.defcon_level,
        game_ended=world.game_ended,
        game_end_reason=world.game_end_reason,
        game_end_message=world.game_end_message,
        game_end_message_fr=world.game_end_message_fr,
        final_score=world.final_score,
        unread_events=timeline.get_unread_count(),  # NEW: unread timeline events
        timeline_total=len(timeline.events),  # NEW: total timeline events
    )


@router.get("/country/{country_id}", response_model=CountryResponse)
async def get_country(country_id: str):
    """Get details of a specific country"""
    world = get_world()
    country = world.get_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    return CountryResponse.from_country(country)


@router.get("/events", response_model=list[EventResponse])
async def get_events(count: int = 50):
    """Get recent events"""
    world = get_world()
    events = world.get_recent_events(count)
    return [EventResponse.from_event(e) for e in events]


@router.post("/tick", response_model=MonthlyTickResponse)
async def advance_tick():
    """Advance simulation by one MONTH (with timeline events)"""
    world = get_world()
    event_pool = get_event_pool()
    timeline = get_timeline()

    old_year = world.year
    old_month = world.month

    # Process monthly tick with timeline
    events, timeline_events, game_end_state = process_tick(world, event_pool, timeline)

    event_responses = [EventResponse.from_event(e) for e in events]

    # Convert timeline events to brief format
    timeline_briefs = [
        TimelineEventBrief(
            id=te.id,
            date=str(te.date),
            actor_country=te.actor_country,
            title_fr=te.title_fr,
            type=te.type if isinstance(te.type, str) else te.type.value,
            importance=te.importance
        )
        for te in timeline_events
    ]

    decisions = len([e for e in events if e.type == "decision"])
    crises = len([e for e in events if e.type == "crisis"])
    diplomacy = len([e for e in events if e.type in ("diplomacy", "sanctions")])

    month_names_fr = [
        "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"
    ]
    month_name = month_names_fr[old_month - 1]

    summary = f"{month_name} {old_year}: {len(timeline_events)} events"
    summary_fr = f"{month_name} {old_year}: {len(timeline_events)} evenements"

    if game_end_state:
        summary += f" - GAME ENDED: {game_end_state.message}"
        summary_fr += f" - FIN DE PARTIE: {game_end_state.message_fr}"

    logger.info(f"Monthly tick: {old_month}/{old_year} -> {world.month}/{world.year} ({len(timeline_events)} timeline events)")

    return MonthlyTickResponse(
        year=world.year,
        month=world.month,
        date_display=world.date_display_en,
        date_display_fr=world.date_display,
        events=event_responses,
        timeline_events=timeline_briefs,
        summary=summary,
        summary_fr=summary_fr,
        game_ended=world.game_ended,
        game_end_reason=world.game_end_reason,
        game_end_message=world.game_end_message,
        game_end_message_fr=world.game_end_message_fr,
        is_victory=game_end_state.is_victory if game_end_state else False,
        final_score=world.final_score,
        defcon_level=world.defcon_level,
        unread_events=timeline.get_unread_count()
    )


@router.post("/tick/year", response_model=TickResponse)
async def advance_tick_year():
    """Advance simulation by one YEAR (12 months) - legacy compatibility"""
    world = get_world()
    event_pool = get_event_pool()

    old_year = world.year

    # Use legacy tick that processes 12 months
    events, game_end_state = process_tick_legacy(world, event_pool)

    event_responses = [EventResponse.from_event(e) for e in events]

    decisions = len([e for e in events if e.type == "decision"])
    crises = len([e for e in events if e.type == "crisis"])
    diplomacy = len([e for e in events if e.type in ("diplomacy", "sanctions")])

    summary = f"Year {old_year}: {decisions} decisions, {crises} crises, {diplomacy} diplomatic events"
    summary_fr = f"Annee {old_year}: {decisions} decisions, {crises} crises, {diplomacy} evenements diplomatiques"

    if game_end_state:
        summary += f" - GAME ENDED: {game_end_state.message}"
        summary_fr += f" - FIN DE PARTIE: {game_end_state.message_fr}"

    logger.info(f"Yearly tick completed: {summary}")

    return TickResponse(
        year=world.year,
        events=event_responses,
        summary=summary,
        summary_fr=summary_fr,
        game_ended=world.game_ended,
        game_end_reason=world.game_end_reason,
        game_end_message=world.game_end_message,
        game_end_message_fr=world.game_end_message_fr,
        is_victory=game_end_state.is_victory if game_end_state else False,
        final_score=world.final_score,
        defcon_level=world.defcon_level,
    )


@router.post("/tick/{years}", response_model=list[TickResponse])
async def advance_multiple_ticks(years: int):
    """Advance simulation by multiple years (stops early if game ends)"""
    if years < 1 or years > 100:
        raise HTTPException(status_code=400, detail="Years must be between 1 and 100")

    results = []
    for _ in range(years):
        result = await advance_tick()
        results.append(result)
        # Stop if game ended
        if result.game_ended:
            break

    return results


@router.post("/reset")
async def reset_world_endpoint(seed: int = 42):
    """Reset the world to initial state"""
    world = reset_world(seed)
    return {"status": "ok", "year": world.year, "seed": seed}


@router.get("/influence-zones", response_model=list[InfluenceZoneResponse])
async def get_influence_zones():
    """Get all influence zones"""
    world = get_world()
    return [InfluenceZoneResponse.from_zone(z) for z in world.influence_zones.values()]


@router.get("/superpowers", response_model=list[CountryResponse])
async def get_superpowers():
    """Get tier 1 superpowers"""
    world = get_world()
    return [CountryResponse.from_country(c) for c in world.get_superpowers()]


@router.get("/nuclear-powers", response_model=list[CountryResponse])
async def get_nuclear_powers():
    """Get all nuclear-armed countries"""
    world = get_world()
    return [CountryResponse.from_country(c) for c in world.get_nuclear_powers()]


@router.get("/bloc/{bloc_name}", response_model=list[CountryResponse])
async def get_bloc_members(bloc_name: str):
    """Get all countries in a specific bloc"""
    world = get_world()
    members = world.get_bloc_members(bloc_name.upper())
    if not members:
        raise HTTPException(status_code=404, detail=f"Bloc {bloc_name} not found or empty")
    return [CountryResponse.from_country(c) for c in members]


# Phase 13: Unified architecture management endpoints

@router.post("/unified-mode")
async def toggle_unified_mode(enabled: bool = True):
    """Enable or disable unified architecture mode (Phase 12/13)"""
    set_unified_mode(enabled)
    world = get_world()  # Forces reload with new mode
    return {
        "status": "ok",
        "unified_mode": is_unified_mode(),
        "world_type": "UnifiedWorld" if is_unified_mode() else "World",
        "total_countries": len(world.countries) if hasattr(world, "countries") else 0,
    }


@router.get("/unified-mode")
async def get_unified_mode_status():
    """Get current unified mode status"""
    world = get_world()
    result = {
        "unified_mode": is_unified_mode(),
        "world_type": type(world).__name__,
        "year": world.year,
    }

    # Add tier stats if in unified mode
    if is_unified_mode() and isinstance(world, UnifiedWorld):
        result["tier_stats"] = world.get_tier_stats()
        result["tick_counter"] = world.tick_counter

    return result


@router.get("/tier-stats")
async def get_tier_stats():
    """Get tier distribution statistics (unified mode only)"""
    world = get_world()
    if not is_unified_mode() or not isinstance(world, UnifiedWorld):
        raise HTTPException(
            status_code=400,
            detail="Tier stats only available in unified mode. Enable with POST /api/unified-mode?enabled=true"
        )

    stats = world.get_tier_stats()
    countries_by_tier = {}
    for tier in range(1, 7):
        countries_by_tier[f"tier_{tier}"] = [
            {"id": c.id, "name": c.name, "power_score": c.get_power_score()}
            for c in world.get_countries_by_tier(tier)
        ]

    return {
        "distribution": stats,
        "countries_by_tier": countries_by_tier,
        "tick_counter": world.tick_counter,
    }
