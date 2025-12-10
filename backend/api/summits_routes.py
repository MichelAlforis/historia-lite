"""Summits routes for Historia Lite"""
from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from engine.summit import summit_manager, SpecialEvent
from api.game_state import get_world

router = APIRouter(prefix="/api", tags=["summits"])


class SummitTypeResponse(BaseModel):
    """Response schema for a summit type"""
    id: str
    name: str
    name_fr: str
    frequency: str
    bloc_id: Optional[str]
    mandatory_participants: List[str] | str
    rotating_host: bool
    host_order: List[str]
    agenda_topics: List[str]
    can_invite_guests: bool
    max_guests: int
    description_fr: str


class ActiveSummitResponse(BaseModel):
    """Response schema for an active/past summit"""
    id: str
    summit_type_id: str
    year: int
    host_country: str
    participants: List[str]
    guests: List[str]
    resolutions_passed: int
    outcomes: List[str]
    status: str


class UpcomingSummitResponse(BaseModel):
    """Response for upcoming summits"""
    year: int
    summit_type: str
    name_fr: str


class SpecialEventResponse(BaseModel):
    """Response for special events"""
    id: str
    name: str
    name_fr: str
    frequency: str
    next_occurrence: Optional[int]
    effects: Dict
    description_fr: str


@router.get("/summits/types", response_model=List[SummitTypeResponse])
async def get_summit_types():
    """Get all summit types"""
    summit_types = list(summit_manager.summit_types.values())
    return [
        SummitTypeResponse(
            id=st.id,
            name=st.name,
            name_fr=st.name_fr,
            frequency=st.frequency,
            bloc_id=st.bloc_id,
            mandatory_participants=st.mandatory_participants,
            rotating_host=st.rotating_host,
            host_order=st.host_order,
            agenda_topics=st.agenda_topics,
            can_invite_guests=st.can_invite_guests,
            max_guests=st.max_guests,
            description_fr=st.description_fr
        )
        for st in summit_types
    ]


@router.get("/summits/upcoming", response_model=List[UpcomingSummitResponse])
async def get_upcoming_summits(years: int = 5):
    """Get upcoming summits for the next N years"""
    world = get_world()
    upcoming = summit_manager.get_upcoming_summits(world.year, count=years)
    return [
        UpcomingSummitResponse(
            year=s["year"],
            summit_type=s["summit_type"],
            name_fr=s["name_fr"]
        )
        for s in upcoming
    ]


@router.get("/summits/scheduled")
async def get_scheduled_summits():
    """Get summits scheduled for the current year"""
    world = get_world()
    scheduled = summit_manager.get_scheduled_summits(world.year)
    return {
        "year": world.year,
        "scheduled_summits": scheduled,
        "count": len(scheduled)
    }


@router.get("/summits/history", response_model=List[ActiveSummitResponse])
async def get_summit_history(limit: int = 20):
    """Get history of past summits"""
    history = summit_manager.summit_history[-limit:]
    return [
        ActiveSummitResponse(
            id=s.id,
            summit_type_id=s.summit_type_id,
            year=s.year,
            host_country=s.host_country,
            participants=s.participants,
            guests=s.guests,
            resolutions_passed=len([r for r in s.resolutions if r.passed]),
            outcomes=s.outcomes,
            status=s.status
        )
        for s in reversed(history)
    ]


@router.get("/summits/active", response_model=List[ActiveSummitResponse])
async def get_active_summits():
    """Get currently active summits"""
    return [
        ActiveSummitResponse(
            id=s.id,
            summit_type_id=s.summit_type_id,
            year=s.year,
            host_country=s.host_country,
            participants=s.participants,
            guests=s.guests,
            resolutions_passed=len([r for r in s.resolutions if r.passed]),
            outcomes=s.outcomes,
            status=s.status
        )
        for s in summit_manager.active_summits
    ]


@router.get("/summits/special-events", response_model=List[SpecialEventResponse])
async def get_special_events():
    """Get special events (World Cup, Olympics, etc.)"""
    world = get_world()
    events = list(summit_manager.special_events.values())

    def next_occurrence(event: SpecialEvent, current_year: int) -> Optional[int]:
        if event.frequency == "every_4_years":
            if event.start_year is None:
                return None
            years_since = (current_year - event.start_year) % 4
            if years_since == 0:
                return current_year
            return current_year + (4 - years_since)
        elif event.frequency == "annual":
            return current_year
        return None

    return [
        SpecialEventResponse(
            id=e.id,
            name=e.name,
            name_fr=e.name_fr,
            frequency=e.frequency,
            next_occurrence=next_occurrence(e, world.year),
            effects=e.effects,
            description_fr=e.description_fr
        )
        for e in events
    ]


@router.get("/summits/country/{country_id}/participation")
async def get_country_summit_participation(country_id: str):
    """Get summit participation info for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    participates_in = []
    for st_id, st in summit_manager.summit_types.items():
        if st.mandatory_participants == "all":
            participates_in.append(st_id)
        elif isinstance(st.mandatory_participants, list):
            if country_id.upper() in st.mandatory_participants:
                participates_in.append(st_id)

    past_count = sum(
        1 for s in summit_manager.summit_history
        if country_id.upper() in s.participants
    )

    hosted_count = sum(
        1 for s in summit_manager.summit_history
        if s.host_country == country_id.upper()
    )

    return {
        "country_id": country_id.upper(),
        "member_of_summits": participates_in,
        "past_participations": past_count,
        "times_hosted": hosted_count
    }
