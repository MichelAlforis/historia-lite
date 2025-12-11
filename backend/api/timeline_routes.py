"""Timeline API routes for Historia Lite"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.game_state import get_world, get_timeline
from engine.world import GameDate
from engine.timeline import TimelineEvent, EventType, EventSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


# Response models
class GameDateResponse(BaseModel):
    year: int
    month: int
    day: int
    display: str
    display_fr: str

    @classmethod
    def from_game_date(cls, date: GameDate) -> "GameDateResponse":
        return cls(
            year=date.year,
            month=date.month,
            day=date.day,
            display=str(date),
            display_fr=date.to_french()
        )


class TimelineEventResponse(BaseModel):
    id: str
    date: GameDateResponse
    actor_country: str
    target_countries: List[str]
    title: str
    title_fr: str
    description: str
    description_fr: str
    type: str
    source: str
    importance: int
    read: bool
    caused_by: Optional[str] = None
    triggers: List[str]

    @classmethod
    def from_timeline_event(cls, event: TimelineEvent) -> "TimelineEventResponse":
        return cls(
            id=event.id,
            date=GameDateResponse.from_game_date(event.date),
            actor_country=event.actor_country,
            target_countries=event.target_countries,
            title=event.title,
            title_fr=event.title_fr,
            description=event.description,
            description_fr=event.description_fr,
            type=event.type if isinstance(event.type, str) else event.type.value,
            source=event.source if isinstance(event.source, str) else event.source.value,
            importance=event.importance,
            read=event.read,
            caused_by=event.caused_by,
            triggers=event.triggers
        )


class TimelineSummaryResponse(BaseModel):
    total_events: int
    unread_count: int
    pending_effects: int
    current_date: GameDateResponse
    recent_events: List[TimelineEventResponse]


class TimelineContextResponse(BaseModel):
    current_date: GameDateResponse
    context_text: str
    event_count: int
    events: List[TimelineEventResponse]


@router.get("/current-date")
async def get_current_date() -> GameDateResponse:
    """Get the current game date"""
    world = get_world()
    return GameDateResponse.from_game_date(world.current_date)


@router.get("/summary")
async def get_timeline_summary() -> TimelineSummaryResponse:
    """Get a summary of the timeline"""
    world = get_world()
    timeline = get_timeline()
    summary = timeline.get_timeline_summary(world.current_date)

    recent = [
        TimelineEventResponse.from_timeline_event(
            timeline.get_event_by_id(e["id"])
        )
        for e in summary["recent_events"]
        if timeline.get_event_by_id(e["id"])
    ]

    return TimelineSummaryResponse(
        total_events=summary["total_events"],
        unread_count=summary["unread_count"],
        pending_effects=summary["pending_effects"],
        current_date=GameDateResponse.from_game_date(world.current_date),
        recent_events=recent
    )


@router.get("/events")
async def get_timeline_events(
    start_year: Optional[int] = None,
    start_month: Optional[int] = None,
    end_year: Optional[int] = None,
    end_month: Optional[int] = None,
    event_type: Optional[str] = None,
    country: Optional[str] = None,
    min_importance: int = Query(default=1, ge=1, le=5),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
) -> List[TimelineEventResponse]:
    """Get timeline events with filters"""
    world = get_world()
    timeline = get_timeline()

    # Default to full timeline if no dates specified
    if start_year is None:
        start_year = world.start_year
        start_month = world.start_month
    if end_year is None:
        end_year = world.year
        end_month = world.month

    start_date = GameDate(year=start_year, month=start_month or 1, day=1)
    end_date = GameDate(year=end_year, month=end_month or 12, day=28)

    # Parse event types
    event_types = None
    if event_type:
        try:
            event_types = [EventType(event_type)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")

    # Parse countries
    countries = None
    if country:
        countries = [country.upper()]

    events = timeline.get_events_for_period(
        start=start_date,
        end=end_date,
        event_types=event_types,
        countries=countries,
        min_importance=min_importance
    )

    # Apply pagination
    paginated = events[offset:offset + limit]

    return [TimelineEventResponse.from_timeline_event(e) for e in paginated]


@router.get("/events/month/{year}/{month}")
async def get_events_for_month(year: int, month: int) -> List[TimelineEventResponse]:
    """Get all events for a specific month"""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    timeline = get_timeline()
    events = timeline.get_events_for_month(year, month)

    return [TimelineEventResponse.from_timeline_event(e) for e in events]


@router.get("/events/country/{country_id}")
async def get_events_for_country(
    country_id: str,
    lookback_months: int = Query(default=6, ge=1, le=24)
) -> List[TimelineEventResponse]:
    """Get recent events involving a specific country"""
    world = get_world()
    timeline = get_timeline()

    events = timeline.get_events_involving_country(
        country_id=country_id.upper(),
        lookback_months=lookback_months,
        current_date=world.current_date
    )

    return [TimelineEventResponse.from_timeline_event(e) for e in events]


@router.get("/event/{event_id}")
async def get_event(event_id: str) -> TimelineEventResponse:
    """Get a specific event by ID"""
    timeline = get_timeline()
    event = timeline.get_event_by_id(event_id)

    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    return TimelineEventResponse.from_timeline_event(event)


@router.get("/event/{event_id}/chain")
async def get_event_chain(event_id: str) -> List[TimelineEventResponse]:
    """Get the chain of events (causes and consequences) for an event"""
    timeline = get_timeline()
    chain = timeline.get_event_chain(event_id)

    if not chain:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")

    return [TimelineEventResponse.from_timeline_event(e) for e in chain]


@router.get("/context")
async def get_ai_context(
    lookback_months: int = Query(default=6, ge=1, le=24),
    max_events: int = Query(default=20, ge=5, le=50)
) -> TimelineContextResponse:
    """Get timeline context for AI prompts"""
    world = get_world()
    timeline = get_timeline()

    context_text = timeline.get_context_for_ai(
        current_date=world.current_date,
        lookback_months=lookback_months,
        max_events=max_events
    )

    recent_events = timeline.get_recent_events(
        current_date=world.current_date,
        lookback_months=lookback_months,
        limit=max_events
    )

    return TimelineContextResponse(
        current_date=GameDateResponse.from_game_date(world.current_date),
        context_text=context_text,
        event_count=len(recent_events),
        events=[TimelineEventResponse.from_timeline_event(e) for e in recent_events]
    )


@router.post("/mark-read")
async def mark_events_as_read(up_to_year: Optional[int] = None, up_to_month: Optional[int] = None):
    """Mark events as read up to a specific date"""
    world = get_world()
    timeline = get_timeline()

    up_to_date = None
    if up_to_year is not None:
        up_to_date = GameDate(
            year=up_to_year,
            month=up_to_month or world.month,
            day=28
        )

    timeline.mark_events_as_read(up_to_date)

    return {"status": "ok", "unread_remaining": timeline.get_unread_count()}


@router.get("/stats")
async def get_timeline_stats():
    """Get statistics about the timeline"""
    world = get_world()
    timeline = get_timeline()

    # Count by type
    type_counts = {}
    for event in timeline.events:
        etype = event.type if isinstance(event.type, str) else event.type.value
        type_counts[etype] = type_counts.get(etype, 0) + 1

    # Count by source
    source_counts = {}
    for event in timeline.events:
        source = event.source if isinstance(event.source, str) else event.source.value
        source_counts[source] = source_counts.get(source, 0) + 1

    # Count by country
    country_counts = {}
    for event in timeline.events:
        country_counts[event.actor_country] = country_counts.get(event.actor_country, 0) + 1

    # Top 10 countries
    top_countries = sorted(country_counts.items(), key=lambda x: -x[1])[:10]

    return {
        "total_events": len(timeline.events),
        "unread_count": timeline.get_unread_count(),
        "pending_effects": len([e for e in timeline.pending_effects if not e.applied]),
        "events_by_type": type_counts,
        "events_by_source": source_counts,
        "top_countries": dict(top_countries),
        "current_date": GameDateResponse.from_game_date(world.current_date).model_dump()
    }


# =============================================================================
# PHASE 2 - INTELLIGENT FILTERING & STRATEGIC TIMELINE (Axes 7-8)
# =============================================================================

@router.get("/highlights/{year}/{month}")
async def get_monthly_highlights(
    year: int,
    month: int,
    player_country: Optional[str] = None
):
    """
    Get auto-generated monthly highlights.
    Includes top events, trends, and summary.
    """
    from engine.timeline import generate_monthly_highlights

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    timeline = get_timeline()
    highlights = generate_monthly_highlights(
        timeline=timeline,
        year=year,
        month=month,
        player_country=player_country.upper() if player_country else None
    )

    return highlights.model_dump()


@router.get("/grouped/{year}/{month}")
async def get_grouped_events(
    year: int,
    month: int,
    player_country: Optional[str] = None
):
    """
    Get events grouped by category to reduce information overload.
    Critical events and player-related events are always separate.
    Minor events are grouped by region.
    """
    from engine.timeline import get_grouped_events as get_grouped

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    timeline = get_timeline()
    grouped = get_grouped(
        timeline=timeline,
        year=year,
        month=month,
        player_country=player_country.upper() if player_country else None
    )

    # Serialize events to dicts
    result = {
        "critical": [TimelineEventResponse.from_timeline_event(e).model_dump() for e in grouped.critical],
        "player_related": [TimelineEventResponse.from_timeline_event(e).model_dump() for e in grouped.player_related],
        "by_region": {
            region: [TimelineEventResponse.from_timeline_event(e).model_dump() for e in events]
            for region, events in grouped.by_region.items()
        },
        "by_type": {
            etype: [TimelineEventResponse.from_timeline_event(e).model_dump() for e in events]
            for etype, events in grouped.by_type.items()
        },
        "merged_minor": grouped.merged_minor
    }

    return result


@router.get("/trends")
async def get_timeline_trends(
    lookback_months: int = Query(default=6, ge=1, le=24),
    player_country: Optional[str] = None
):
    """
    Analyze timeline trends for strategic decision-making.
    Identifies rising tensions, active actors, and generates alerts.
    """
    from engine.timeline import analyze_trends

    world = get_world()
    timeline = get_timeline()

    trends = analyze_trends(
        timeline=timeline,
        current_date=world.current_date,
        lookback_months=lookback_months,
        player_country=player_country.upper() if player_country else None
    )

    return {
        "tension_trends": [t.model_dump() for t in trends.tension_trends],
        "most_active_actors": trends.most_active_actors,
        "rising_event_types": trends.rising_event_types,
        "ai_predictions": trends.ai_predictions,
        "alerts": trends.alerts,
        "total_events_analyzed": trends.total_events_analyzed,
        "period_months": trends.period_months,
        "avg_events_per_month": trends.avg_events_per_month
    }


@router.get("/strategic-overview")
async def get_strategic_overview(
    player_country: Optional[str] = None
):
    """
    Get a complete strategic overview combining:
    - Timeline trends
    - Active crises
    - World mood/era
    - Monthly highlights
    """
    from engine.timeline import get_strategic_overview as get_overview
    from api.game_state import get_crisis_manager, get_world_mood

    world = get_world()
    timeline = get_timeline()
    crisis_manager = get_crisis_manager()
    world_mood = get_world_mood()

    overview = get_overview(
        timeline=timeline,
        current_date=world.current_date,
        crisis_manager=crisis_manager,
        world_mood=world_mood,
        player_country=player_country.upper() if player_country else None
    )

    return overview


@router.get("/alerts")
async def get_active_alerts(
    player_country: Optional[str] = None,
    min_severity: int = Query(default=0, ge=0, le=100)
):
    """
    Get active alerts from timeline analysis.
    Filter by severity level.
    """
    from engine.timeline import analyze_trends

    world = get_world()
    timeline = get_timeline()

    trends = analyze_trends(
        timeline=timeline,
        current_date=world.current_date,
        lookback_months=6,
        player_country=player_country.upper() if player_country else None
    )

    # Filter by severity
    alerts = [a for a in trends.alerts if a.get("severity", 0) >= min_severity]

    # Sort by severity (highest first)
    alerts.sort(key=lambda a: a.get("severity", 0), reverse=True)

    return {
        "alerts": alerts,
        "total_count": len(trends.alerts),
        "filtered_count": len(alerts),
        "danger_count": sum(1 for a in alerts if a.get("level") == "danger"),
        "warning_count": sum(1 for a in alerts if a.get("level") == "warning"),
        "positive_count": sum(1 for a in alerts if a.get("level") == "positive")
    }


@router.get("/tension/{country_a}/{country_b}")
async def get_tension_between_countries(
    country_a: str,
    country_b: str,
    lookback_months: int = Query(default=12, ge=1, le=36)
):
    """
    Get tension history and trend between two specific countries.
    """
    from engine.timeline import analyze_trends, _make_pair_key

    world = get_world()
    timeline = get_timeline()

    country_a = country_a.upper()
    country_b = country_b.upper()
    pair_key = _make_pair_key(country_a, country_b)

    trends = analyze_trends(
        timeline=timeline,
        current_date=world.current_date,
        lookback_months=lookback_months
    )

    # Find the specific pair
    pair_trend = None
    for trend in trends.tension_trends:
        if trend.pair == pair_key:
            pair_trend = trend
            break

    if not pair_trend:
        return {
            "pair": pair_key,
            "country_a": country_a,
            "country_b": country_b,
            "tension_delta": 0,
            "event_count": 0,
            "recent_events": [],
            "status": "neutral",
            "message": f"Aucun evenement entre {country_a} et {country_b} sur les {lookback_months} derniers mois"
        }

    # Determine status
    status = "neutral"
    if pair_trend.tension_delta > 15:
        status = "hostile"
    elif pair_trend.tension_delta > 5:
        status = "tense"
    elif pair_trend.tension_delta < -10:
        status = "improving"
    elif pair_trend.tension_delta < -5:
        status = "cooperative"

    return {
        "pair": pair_key,
        "country_a": pair_trend.country_a,
        "country_b": pair_trend.country_b,
        "tension_delta": pair_trend.tension_delta,
        "event_count": pair_trend.event_count,
        "recent_events": pair_trend.recent_events,
        "status": status,
        "message": _get_tension_message(pair_trend.tension_delta, country_a, country_b)
    }


def _get_tension_message(delta: float, country_a: str, country_b: str) -> str:
    """Generate a human-readable message about tension between countries"""
    if delta > 20:
        return f"Relations tres tendues entre {country_a} et {country_b}. Risque de conflit eleve."
    elif delta > 10:
        return f"Tensions en hausse entre {country_a} et {country_b}."
    elif delta > 0:
        return f"Legeres tensions entre {country_a} et {country_b}."
    elif delta < -15:
        return f"Forte amelioration des relations {country_a}-{country_b}."
    elif delta < -5:
        return f"Relations {country_a}-{country_b} en amelioration."
    else:
        return f"Relations stables entre {country_a} et {country_b}."
