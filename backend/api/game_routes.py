"""Core game routes for Historia Lite - state, tick, reset, countries"""
import logging
from fastapi import APIRouter, HTTPException

from engine.tick import process_tick
from schemas.game import (
    WorldStateResponse,
    CountryResponse,
    InfluenceZoneResponse,
    EventResponse,
    ConflictResponse,
    TickResponse,
)
from api.game_state import get_world, get_event_pool, reset_world

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["game"])


@router.get("/state", response_model=WorldStateResponse)
async def get_state():
    """Get the current world state"""
    world = get_world()

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

    return WorldStateResponse(
        year=world.year,
        seed=world.seed,
        oil_price=world.oil_price,
        global_tension=world.global_tension,
        countries=countries,
        influence_zones=zones,
        active_conflicts=conflicts,
        recent_events=recent_events,
        total_countries=len(world.countries) + len(world.tier4_countries),
        nuclear_powers=len(world.get_nuclear_powers()),
        active_wars=len(world.active_conflicts),
        tier4_count=len(world.tier4_countries),
        tier4_in_crisis=tier4_in_crisis,
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


@router.post("/tick", response_model=TickResponse)
async def advance_tick():
    """Advance simulation by one year"""
    world = get_world()
    event_pool = get_event_pool()

    old_year = world.year
    events = process_tick(world, event_pool)

    event_responses = [EventResponse.from_event(e) for e in events]

    decisions = len([e for e in events if e.type == "decision"])
    crises = len([e for e in events if e.type == "crisis"])
    diplomacy = len([e for e in events if e.type in ("diplomacy", "sanctions")])

    summary = f"Year {old_year}: {decisions} decisions, {crises} crises, {diplomacy} diplomatic events"
    summary_fr = f"Annee {old_year}: {decisions} decisions, {crises} crises, {diplomacy} evenements diplomatiques"

    logger.info(f"Tick completed: {summary}")

    return TickResponse(
        year=world.year,
        events=event_responses,
        summary=summary,
        summary_fr=summary_fr,
    )


@router.post("/tick/{years}", response_model=list[TickResponse])
async def advance_multiple_ticks(years: int):
    """Advance simulation by multiple years"""
    if years < 1 or years > 100:
        raise HTTPException(status_code=400, detail="Years must be between 1 and 100")

    results = []
    for _ in range(years):
        result = await advance_tick()
        results.append(result)

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
