"""Timeline Engine for Historia Lite - Central backbone for time-based gameplay"""
import logging
import random
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .world import GameDate

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of timeline events"""
    WAR = "war"
    DIPLOMATIC = "diplomatic"
    ECONOMIC = "economic"
    POLITICAL = "political"
    MILITARY = "military"
    INTERNAL = "internal"
    TECHNOLOGY = "technology"
    CULTURAL = "cultural"
    CRISIS = "crisis"
    PLAYER_ACTION = "player_action"


class EventSource(str, Enum):
    """Source of timeline events"""
    HISTORICAL = "historical"
    PROCEDURAL = "procedural"
    PLAYER = "player"
    AI_GENERATED = "ai_generated"
    SYSTEM = "system"


class TimelineEvent(BaseModel):
    """A single event in the game timeline with rich narrative content"""
    id: str
    date: GameDate

    # Actor and targets
    actor_country: str  # Country code (FRA, USA, etc.)
    target_countries: List[str] = Field(default_factory=list)

    # Narrative content
    title: str
    title_fr: str
    description: str  # Detailed narrative (2-4 sentences)
    description_fr: str

    # Metadata
    type: EventType = EventType.POLITICAL
    source: EventSource = EventSource.SYSTEM
    importance: int = Field(default=3, ge=1, le=5)  # 5 = critical

    # Effects on world state
    effects: Dict[str, Any] = Field(default_factory=dict)

    # Event chaining
    caused_by: Optional[str] = None  # ID of triggering event
    triggers: List[str] = Field(default_factory=list)  # IDs of triggered events

    # UI state
    read: bool = False

    class Config:
        use_enum_values = True


class DelayedEffect(BaseModel):
    """An effect that will be applied at a future date"""
    id: str
    trigger_date: GameDate
    source_event_id: str
    target_country: str
    effects: Dict[str, int]  # stat_name -> delta
    description: str
    description_fr: str
    applied: bool = False


class TimelineManager:
    """Central manager for the game timeline - the backbone of time-based gameplay"""

    def __init__(self):
        self.events: List[TimelineEvent] = []
        self.pending_effects: List[DelayedEffect] = []
        self._event_id_counter: int = 0

    def generate_event_id(self, prefix: str = "evt") -> str:
        """Generate a unique event ID"""
        self._event_id_counter += 1
        return f"{prefix}_{self._event_id_counter}"

    def add_event(self, event: TimelineEvent) -> None:
        """Add an event to the timeline"""
        self.events.append(event)
        self.events.sort(key=lambda e: e.date.to_ordinal())
        logger.debug(f"Timeline: Added event {event.id} on {event.date}")

    def add_events(self, events: List[TimelineEvent]) -> None:
        """Add multiple events to the timeline"""
        for event in events:
            self.add_event(event)

    def get_events_for_period(
        self,
        start: GameDate,
        end: GameDate,
        event_types: Optional[List[EventType]] = None,
        countries: Optional[List[str]] = None,
        min_importance: int = 1
    ) -> List[TimelineEvent]:
        """Get events within a date range with optional filters"""
        filtered = []
        for event in self.events:
            # Date filter
            if event.date < start or event.date > end:
                continue
            # Type filter
            if event_types and event.type not in event_types:
                continue
            # Country filter
            if countries:
                involved = [event.actor_country] + event.target_countries
                if not any(c in countries for c in involved):
                    continue
            # Importance filter
            if event.importance < min_importance:
                continue
            filtered.append(event)
        return filtered

    def get_events_for_month(self, year: int, month: int) -> List[TimelineEvent]:
        """Get all events for a specific month"""
        return [e for e in self.events if e.date.year == year and e.date.month == month]

    def get_events_involving_country(
        self,
        country_id: str,
        lookback_months: int = 6,
        current_date: Optional[GameDate] = None
    ) -> List[TimelineEvent]:
        """Get recent events involving a specific country"""
        if current_date is None:
            return []
        start_date = current_date.subtract_months(lookback_months)
        events = []
        for event in self.events:
            if event.date < start_date or event.date > current_date:
                continue
            if event.actor_country == country_id or country_id in event.target_countries:
                events.append(event)
        return events

    def get_recent_events(
        self,
        current_date: GameDate,
        lookback_months: int = 3,
        limit: int = 50
    ) -> List[TimelineEvent]:
        """Get recent events for AI context"""
        start_date = current_date.subtract_months(lookback_months)
        filtered = [e for e in self.events if start_date <= e.date <= current_date]
        # Sort by importance then date (most recent first)
        filtered.sort(key=lambda e: (-e.importance, -e.date.to_ordinal()))
        return filtered[:limit]

    def get_unread_count(self) -> int:
        """Get count of unread events"""
        return sum(1 for e in self.events if not e.read)

    def mark_events_as_read(self, up_to_date: Optional[GameDate] = None) -> None:
        """Mark events as read"""
        for event in self.events:
            if up_to_date is None or event.date <= up_to_date:
                event.read = True

    def add_delayed_effect(self, effect: DelayedEffect) -> None:
        """Add an effect to be applied at a future date"""
        self.pending_effects.append(effect)
        logger.debug(f"Timeline: Added delayed effect {effect.id} for {effect.trigger_date}")

    def process_delayed_effects(self, current_date: GameDate) -> List[DelayedEffect]:
        """Process and return effects that should be applied now"""
        to_apply = []
        for effect in self.pending_effects:
            if not effect.applied and effect.trigger_date <= current_date:
                effect.applied = True
                to_apply.append(effect)
        return to_apply

    def get_context_for_ai(
        self,
        current_date: GameDate,
        lookback_months: int = 6,
        max_events: int = 20
    ) -> str:
        """Generate timeline context string for AI prompts"""
        events = self.get_recent_events(current_date, lookback_months, max_events)
        if not events:
            return "No significant events in recent history."

        lines = []
        for event in events:
            date_str = str(event.date)
            lines.append(f"- {date_str}: [{event.actor_country}] {event.title}")
            if event.target_countries:
                lines.append(f"  Targets: {', '.join(event.target_countries)}")
        return "\n".join(lines)

    def get_event_chain(self, event_id: str) -> List[TimelineEvent]:
        """Get all events in a chain (caused_by relationships)"""
        chain = []
        current_id = event_id

        # Go back to find root
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            event = self.get_event_by_id(current_id)
            if event:
                chain.insert(0, event)
                current_id = event.caused_by
            else:
                break

        # Go forward to find consequences
        start_event = self.get_event_by_id(event_id)
        if start_event:
            self._collect_triggered_events(start_event, chain, visited)

        return chain

    def _collect_triggered_events(
        self,
        event: TimelineEvent,
        chain: List[TimelineEvent],
        visited: set
    ) -> None:
        """Recursively collect triggered events"""
        for triggered_id in event.triggers:
            if triggered_id not in visited:
                visited.add(triggered_id)
                triggered_event = self.get_event_by_id(triggered_id)
                if triggered_event:
                    chain.append(triggered_event)
                    self._collect_triggered_events(triggered_event, chain, visited)

    def get_event_by_id(self, event_id: str) -> Optional[TimelineEvent]:
        """Get an event by its ID"""
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def create_event(
        self,
        date: GameDate,
        actor_country: str,
        title: str,
        title_fr: str,
        description: str,
        description_fr: str,
        event_type: EventType = EventType.POLITICAL,
        source: EventSource = EventSource.SYSTEM,
        importance: int = 3,
        target_countries: Optional[List[str]] = None,
        effects: Optional[Dict[str, Any]] = None,
        caused_by: Optional[str] = None
    ) -> TimelineEvent:
        """Helper to create and add an event"""
        event = TimelineEvent(
            id=self.generate_event_id(event_type.value[:3]),
            date=date,
            actor_country=actor_country,
            target_countries=target_countries or [],
            title=title,
            title_fr=title_fr,
            description=description,
            description_fr=description_fr,
            type=event_type,
            source=source,
            importance=importance,
            effects=effects or {},
            caused_by=caused_by
        )
        self.add_event(event)
        return event

    def assign_day_to_events(
        self,
        events: List[TimelineEvent],
        year: int,
        month: int
    ) -> None:
        """Assign days to events that don't have one, spreading them across the month"""
        events_without_day = [e for e in events if e.date.day == 0 or e.date.day == 1]
        if not events_without_day:
            return

        # Spread events across the month (days 1-28 to be safe)
        available_days = list(range(1, 29))
        random.shuffle(available_days)

        for i, event in enumerate(events_without_day):
            if i < len(available_days):
                event.date = GameDate(year=year, month=month, day=available_days[i])

    def get_timeline_summary(self, current_date: GameDate) -> Dict[str, Any]:
        """Get a summary of the timeline for API responses"""
        recent_events = self.get_recent_events(current_date, lookback_months=1, limit=10)
        return {
            "total_events": len(self.events),
            "unread_count": self.get_unread_count(),
            "pending_effects": len([e for e in self.pending_effects if not e.applied]),
            "recent_events": [
                {
                    "id": e.id,
                    "date": str(e.date),
                    "title_fr": e.title_fr,
                    "actor_country": e.actor_country,
                    "type": e.type,
                    "importance": e.importance
                }
                for e in recent_events
            ]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize timeline for storage"""
        return {
            "events": [e.model_dump() for e in self.events],
            "pending_effects": [e.model_dump() for e in self.pending_effects],
            "event_id_counter": self._event_id_counter
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineManager":
        """Deserialize timeline from storage"""
        manager = cls()
        manager.events = [TimelineEvent(**e) for e in data.get("events", [])]
        manager.pending_effects = [DelayedEffect(**e) for e in data.get("pending_effects", [])]
        manager._event_id_counter = data.get("event_id_counter", 0)
        return manager

    def clear(self) -> None:
        """Clear all events and effects"""
        self.events = []
        self.pending_effects = []
        self._event_id_counter = 0
