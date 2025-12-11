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


class EventFamily(str, Enum):
    """The 6 families of timeline events (design: Timeline Backbone)"""
    STRUCTURAL = "structural"      # Long-term shifts (elections, treaties)
    TACTICAL = "tactical"          # Short-term actions (sanctions, deployments)
    OPPORTUNITY = "opportunity"    # Windows of action (summits, crises)
    ESCALATION = "escalation"      # Rising tensions (military buildups)
    NARRATIVE = "narrative"        # Story-driven events (AI-generated arcs)
    PLAYER = "player"              # Player decisions


class CausalLink(BaseModel):
    """A link in a causal chain (cause or effect)"""
    event_id: str
    title: str
    title_fr: str
    date: GameDate
    link_type: str = "direct"  # direct, indirect, probable
    strength: float = 1.0  # 0.0 - 1.0, how strong the causal link is


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
    family: EventFamily = EventFamily.TACTICAL  # Event family category

    # Effects on world state
    effects: Dict[str, Any] = Field(default_factory=dict)

    # Event chaining (causal graph)
    caused_by: Optional[str] = None  # ID of triggering event
    triggers: List[str] = Field(default_factory=list)  # IDs of triggered events
    causal_chain_depth: int = 0  # How many events deep in a chain (0 = root)

    # CAUSAL CHAIN VISUALIZATION (Timeline Backbone design)
    # "voir les 3 causes précédentes" / "voir les 3 conséquences probables"
    caused_by_chain: List[CausalLink] = Field(default_factory=list)  # Previous causes (up to 3)
    effects_chain: List[CausalLink] = Field(default_factory=list)  # Probable effects (up to 3)

    # Ripple effects (cascade system)
    ripple_weight: float = 1.0  # How much this propagates (0.0 - 2.0)
    ripple_targets: List[str] = Field(default_factory=list)  # Countries affected by ripple
    memory_impact: Dict[str, float] = Field(default_factory=dict)  # country -> memory score delta

    # Temporal window
    expiry_date: Optional[GameDate] = None  # After this, event fades from active consideration
    time_window_months: int = 6  # How long this event remains "active" in memory

    # UI state
    read: bool = False

    class Config:
        use_enum_values = True

    def get_memory_decay(self, current_date: GameDate) -> float:
        """Calculate how much this event has decayed in memory (0.0 to 1.0)"""
        months_passed = current_date.months_since(self.date)
        if months_passed >= self.time_window_months:
            return 0.0
        # Linear decay weighted by importance
        base_decay = 1.0 - (months_passed / self.time_window_months)
        importance_bonus = (self.importance - 1) * 0.1  # importance 5 = +0.4 retention
        return min(1.0, base_decay + importance_bonus)

    def affects_country(self, country_id: str) -> bool:
        """Check if this event affects a specific country"""
        return (
            self.actor_country == country_id or
            country_id in self.target_countries or
            country_id in self.ripple_targets
        )


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

    # =========================================================================
    # MULTI-WINDOW AI CONTEXT (3/6/12 months - Timeline Backbone design)
    # =========================================================================

    def get_ai_context_multi_window(
        self,
        current_date: GameDate,
        country_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate multi-window context for AI decision making.
        - 3 months: Immediate tactical decisions
        - 6 months: Doctrinal changes
        - 12 months: Alliance strategies
        - Critical events (importance=5): Major ruptures
        """
        context = {
            "current_date": str(current_date),
            "windows": {
                "tactical_3m": [],
                "doctrinal_6m": [],
                "strategic_12m": [],
                "critical_all": []
            },
            "country_memory": {},
            "active_chains": [],
            "preparation_states": {},
            "summary": ""
        }

        # 3-month window (tactical)
        events_3m = self.get_recent_events(current_date, 3, 15)
        context["windows"]["tactical_3m"] = [
            self._event_to_ai_summary(e, current_date, country_id)
            for e in events_3m
        ]

        # 6-month window (doctrinal)
        events_6m = self.get_recent_events(current_date, 6, 25)
        context["windows"]["doctrinal_6m"] = [
            self._event_to_ai_summary(e, current_date, country_id)
            for e in events_6m if e not in events_3m
        ]

        # 12-month window (strategic)
        events_12m = self.get_recent_events(current_date, 12, 40)
        context["windows"]["strategic_12m"] = [
            self._event_to_ai_summary(e, current_date, country_id)
            for e in events_12m if e not in events_6m
        ]

        # Critical events (importance=5) from all time
        critical = [e for e in self.events if e.importance == 5]
        context["windows"]["critical_all"] = [
            self._event_to_ai_summary(e, current_date, country_id)
            for e in critical[-10:]
        ]

        # Calculate country memory scores
        if country_id:
            context["country_memory"] = self.get_country_memory(country_id, current_date)
            context["preparation_states"] = self.get_preparation_states(country_id, current_date)

        # Find active causal chains
        context["active_chains"] = self._get_active_chains(current_date)

        # Generate summary
        context["summary"] = self._generate_ai_summary(context, country_id)

        return context

    def _event_to_ai_summary(
        self,
        event: TimelineEvent,
        current_date: GameDate,
        observer_country: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert event to AI-readable summary"""
        decay = event.get_memory_decay(current_date) if hasattr(event, 'get_memory_decay') else 1.0
        relevance = decay * event.importance

        affects_observer = observer_country and (
            event.actor_country == observer_country or
            observer_country in event.target_countries
        )

        return {
            "id": event.id,
            "date": str(event.date),
            "actor": event.actor_country,
            "targets": event.target_countries,
            "title": event.title,
            "type": event.type if isinstance(event.type, str) else event.type.value,
            "importance": event.importance,
            "memory_decay": round(decay, 2),
            "relevance_score": round(relevance, 2),
            "affects_observer": affects_observer,
            "caused_by": event.caused_by
        }

    def get_country_memory(
        self,
        country_id: str,
        current_date: GameDate,
        lookback_months: int = 24
    ) -> Dict[str, float]:
        """
        Calculate weighted memory scores for a country.
        Memory influences: diplomacy, aggression, alliances, stability, perception.
        """
        memory = {
            "positive_events": 0.0,
            "negative_events": 0.0,
            "conflicts_suffered": 0.0,
            "conflicts_initiated": 0.0,
            "diplomatic_wins": 0.0,
            "diplomatic_losses": 0.0,
            "total_weighted_impact": 0.0
        }

        start_date = current_date.subtract_months(lookback_months)

        for event in self.events:
            if event.date < start_date or event.date > current_date:
                continue

            is_actor = event.actor_country == country_id
            is_target = country_id in event.target_countries

            if not is_actor and not is_target:
                continue

            decay = event.get_memory_decay(current_date) if hasattr(event, 'get_memory_decay') else 1.0
            weight = decay * event.importance

            event_type = event.type if isinstance(event.type, str) else event.type.value

            if is_actor:
                if event_type in ("war", "military"):
                    memory["conflicts_initiated"] += weight
                elif event_type == "diplomatic":
                    memory["diplomatic_wins"] += weight * 0.5
            elif is_target:
                if event_type in ("war", "military"):
                    memory["conflicts_suffered"] += weight
                elif event_type == "diplomatic":
                    memory["diplomatic_losses"] += weight * 0.3

            memory["total_weighted_impact"] += weight

        return memory

    def get_preparation_states(
        self,
        country_id: str,
        current_date: GameDate
    ) -> Dict[str, Any]:
        """
        Track preparation states for a country (Pax Historia concept).
        A prepared action is faster than a reactive one.
        """
        preparations = {
            "military_mobilization": 0,  # 0-100, affects deployment speed
            "diplomatic_channels": 0,    # 0-100, affects negotiation speed
            "economic_reserves": 0,      # 0-100, affects sanction resilience
            "intelligence_network": 0,   # 0-100, affects info gathering speed
            "prepared_actions": []       # List of actions being prepared
        }

        # Look for preparation events in last 6 months
        start_date = current_date.subtract_months(6)
        for event in self.events:
            if event.date < start_date or event.date > current_date:
                continue
            if event.actor_country != country_id:
                continue

            event_type = event.type if isinstance(event.type, str) else event.type.value

            # Increment preparation based on event types
            if event_type == "military":
                preparations["military_mobilization"] = min(100, preparations["military_mobilization"] + 15)
            elif event_type == "diplomatic":
                preparations["diplomatic_channels"] = min(100, preparations["diplomatic_channels"] + 10)
            elif event_type == "economic":
                preparations["economic_reserves"] = min(100, preparations["economic_reserves"] + 10)

            # Check for explicit preparation in effects
            if hasattr(event, 'effects') and event.effects:
                if "preparation" in event.effects:
                    prep = event.effects["preparation"]
                    preparations["prepared_actions"].append({
                        "type": prep.get("type", "unknown"),
                        "target": prep.get("target"),
                        "ready_date": prep.get("ready_date"),
                        "bonus_speed": prep.get("bonus_speed", 1.5)
                    })

        return preparations

    def calculate_action_speed(
        self,
        country_id: str,
        action_type: str,
        current_date: GameDate
    ) -> float:
        """
        Calculate how fast an action can be executed based on preparation.
        Returns a multiplier (1.0 = normal, 2.0 = twice as fast, 0.5 = half speed).
        """
        preparations = self.get_preparation_states(country_id, current_date)

        base_speed = 1.0

        # Check for specific prepared action
        for prep in preparations["prepared_actions"]:
            if prep["type"] == action_type:
                return prep.get("bonus_speed", 1.5)

        # General preparation bonus
        if action_type == "military" and preparations["military_mobilization"] > 50:
            base_speed += (preparations["military_mobilization"] - 50) / 100  # Max +0.5
        elif action_type == "diplomatic" and preparations["diplomatic_channels"] > 50:
            base_speed += (preparations["diplomatic_channels"] - 50) / 100
        elif action_type == "economic" and preparations["economic_reserves"] > 50:
            base_speed += (preparations["economic_reserves"] - 50) / 100

        return min(2.0, base_speed)  # Cap at 2x speed

    def _get_active_chains(self, current_date: GameDate, max_chains: int = 5) -> List[Dict]:
        """Find active causal chains (events with triggers in last 6 months)"""
        chains = []
        start_date = current_date.subtract_months(6)

        for event in self.events:
            if event.date < start_date:
                continue
            if event.triggers and (not hasattr(event, 'causal_chain_depth') or event.causal_chain_depth == 0):
                chain = self.get_event_chain(event.id)
                if len(chain) >= 2:
                    chains.append({
                        "root_id": event.id,
                        "root_title": event.title_fr,
                        "chain_length": len(chain),
                        "events": [e.id for e in chain]
                    })

        return chains[:max_chains]

    def _generate_ai_summary(
        self,
        context: Dict[str, Any],
        country_id: Optional[str]
    ) -> str:
        """Generate a human-readable summary for AI prompts"""
        lines = [f"=== TIMELINE CONTEXT as of {context['current_date']} ==="]

        tactical = context["windows"]["tactical_3m"]
        if tactical:
            lines.append(f"\n[RECENT - 3 months] {len(tactical)} events:")
            for e in tactical[:5]:
                lines.append(f"  - {e['date']}: [{e['actor']}] {e['title']} (imp:{e['importance']})")

        critical = context["windows"]["critical_all"]
        if critical:
            lines.append(f"\n[CRITICAL EVENTS] {len(critical)} major ruptures:")
            for e in critical[:3]:
                lines.append(f"  * {e['date']}: {e['title']} (IMPORTANCE 5)")

        chains = context.get("active_chains", [])
        if chains:
            lines.append(f"\n[ACTIVE CHAINS] {len(chains)} causal sequences:")
            for c in chains[:2]:
                lines.append(f"  Chain: {c['root_title']} -> {c['chain_length']} events")

        # Preparation states
        preps = context.get("preparation_states", {})
        if preps and country_id:
            lines.append(f"\n[PREPARATION STATE for {country_id}]")
            lines.append(f"  Military readiness: {preps.get('military_mobilization', 0)}%")
            lines.append(f"  Diplomatic channels: {preps.get('diplomatic_channels', 0)}%")

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

    # =========================================================================
    # CAUSAL CONTEXT (Timeline Backbone design)
    # "voir les 3 causes précédentes" / "voir les 3 conséquences probables"
    # =========================================================================

    def get_causal_context(self, event_id: str, max_causes: int = 3, max_effects: int = 3) -> Dict[str, List[CausalLink]]:
        """
        Get the causal context for an event:
        - causes: up to 3 previous events that led to this
        - effects: up to 3 probable consequences
        """
        result = {
            "causes": [],
            "effects": []
        }

        event = self.get_event_by_id(event_id)
        if not event:
            return result

        # Get causes (walk back via caused_by)
        causes = self._get_causes_chain(event, max_causes)
        result["causes"] = causes

        # Get effects (walk forward via triggers, or predict probable effects)
        effects = self._get_effects_chain(event, max_effects)
        result["effects"] = effects

        return result

    def _get_causes_chain(self, event: TimelineEvent, max_depth: int = 3) -> List[CausalLink]:
        """Walk backwards to find the chain of causes"""
        causes = []
        current_id = event.caused_by
        depth = 0
        visited = {event.id}

        while current_id and depth < max_depth and current_id not in visited:
            visited.add(current_id)
            cause_event = self.get_event_by_id(current_id)
            if cause_event:
                link = CausalLink(
                    event_id=cause_event.id,
                    title=cause_event.title,
                    title_fr=cause_event.title_fr,
                    date=cause_event.date,
                    link_type="direct" if depth == 0 else "indirect",
                    strength=1.0 - (depth * 0.2)  # Decreasing strength
                )
                causes.append(link)
                current_id = cause_event.caused_by
                depth += 1
            else:
                break

        return causes

    def _get_effects_chain(self, event: TimelineEvent, max_depth: int = 3) -> List[CausalLink]:
        """Get triggered effects and probable consequences"""
        effects = []
        visited = {event.id}

        # First: actual triggered events
        for triggered_id in event.triggers[:max_depth]:
            if triggered_id in visited:
                continue
            visited.add(triggered_id)
            triggered_event = self.get_event_by_id(triggered_id)
            if triggered_event:
                link = CausalLink(
                    event_id=triggered_event.id,
                    title=triggered_event.title,
                    title_fr=triggered_event.title_fr,
                    date=triggered_event.date,
                    link_type="direct",
                    strength=1.0
                )
                effects.append(link)

        # Second: probable effects (from effects_chain if set, or inferred)
        if len(effects) < max_depth and event.effects_chain:
            for probable in event.effects_chain[: max_depth - len(effects)]:
                if probable.event_id not in visited:
                    effects.append(probable)

        return effects

    def populate_causal_chains(self, event: TimelineEvent) -> None:
        """
        Populate caused_by_chain and effects_chain for an event.
        Called when adding an event or when requesting detailed view.
        """
        context = self.get_causal_context(event.id)
        event.caused_by_chain = context["causes"]
        event.effects_chain = context["effects"]

    def link_events(self, cause_event_id: str, effect_event_id: str, strength: float = 1.0) -> bool:
        """
        Create a causal link between two events.
        Sets caused_by on effect and adds to triggers on cause.
        """
        cause = self.get_event_by_id(cause_event_id)
        effect = self.get_event_by_id(effect_event_id)

        if not cause or not effect:
            return False

        # Set the relationship
        effect.caused_by = cause_event_id
        effect.causal_chain_depth = cause.causal_chain_depth + 1

        if effect_event_id not in cause.triggers:
            cause.triggers.append(effect_event_id)

        # Update causal chains
        self.populate_causal_chains(effect)

        return True

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

    # =========================================================================
    # MEMORY SYSTEM INTEGRATION (Timeline Backbone)
    # =========================================================================

    def update_country_memories(self, event: TimelineEvent, world) -> None:
        """
        Update country memory_scores based on an event.
        Called after adding an event to the timeline.
        """
        if not hasattr(world, 'countries'):
            return

        event_type = event.type if isinstance(event.type, str) else event.type.value
        weight = event.importance * event.ripple_weight

        # Actor country remembers targets
        actor = world.get_any_country(event.actor_country)
        if actor and hasattr(actor, 'update_memory'):
            for target_id in event.target_countries:
                # Determine memory type based on event
                if event_type in ("war", "military"):
                    actor.update_memory(target_id, conflicts=weight * 0.5)
                elif event_type == "diplomatic":
                    # Positive or negative depends on event description/effects
                    if self._is_positive_event(event):
                        actor.update_memory(target_id, diplomatic=weight * 0.3)
                    else:
                        actor.update_memory(target_id, diplomatic=-weight * 0.3)
                elif event_type == "economic":
                    if self._is_positive_event(event):
                        actor.update_memory(target_id, positive=weight * 0.2)
                    else:
                        actor.update_memory(target_id, negative=weight * 0.2)

        # Target countries remember actor
        for target_id in event.target_countries:
            target = world.get_any_country(target_id)
            if target and hasattr(target, 'update_memory'):
                if event_type in ("war", "military"):
                    target.update_memory(event.actor_country, conflicts=weight)
                elif event_type == "diplomatic":
                    if self._is_positive_event(event):
                        target.update_memory(event.actor_country, diplomatic=weight * 0.5)
                    else:
                        target.update_memory(event.actor_country, diplomatic=-weight * 0.5)
                elif event_type == "economic":
                    if self._is_positive_event(event):
                        target.update_memory(event.actor_country, positive=weight * 0.3)
                    else:
                        target.update_memory(event.actor_country, negative=weight * 0.4)

        # Ripple targets also remember (weaker)
        for ripple_id in event.ripple_targets:
            if ripple_id in event.target_countries:
                continue  # Already processed
            ripple_country = world.get_any_country(ripple_id)
            if ripple_country and hasattr(ripple_country, 'update_memory'):
                ripple_weight = weight * 0.3  # Weaker memory for ripple
                if event_type in ("war", "military"):
                    ripple_country.update_memory(event.actor_country, conflicts=ripple_weight * 0.5)
                elif event_type in ("diplomatic", "economic"):
                    if self._is_positive_event(event):
                        ripple_country.update_memory(event.actor_country, positive=ripple_weight * 0.2)
                    else:
                        ripple_country.update_memory(event.actor_country, negative=ripple_weight * 0.2)

    def _is_positive_event(self, event: TimelineEvent) -> bool:
        """Determine if an event is generally positive based on effects and keywords"""
        # Check effects for positive/negative indicators
        if event.effects:
            for country_id, effects in event.effects.items():
                if isinstance(effects, dict):
                    for stat, value in effects.items():
                        if isinstance(value, (int, float)):
                            if value < 0:
                                return False
                            elif value > 0:
                                return True

        # Check title for keywords
        positive_keywords = ["treaty", "accord", "aid", "cooperation", "summit", "peace", "alliance"]
        negative_keywords = ["sanction", "attack", "war", "crisis", "threat", "blockade", "embargo"]

        title_lower = event.title.lower()
        for kw in negative_keywords:
            if kw in title_lower:
                return False
        for kw in positive_keywords:
            if kw in title_lower:
                return True

        return True  # Default to positive

    def decay_all_country_memories(self, world, months_passed: int = 1) -> None:
        """Apply memory decay to all countries (call monthly)"""
        if not hasattr(world, 'countries'):
            return

        for country in world.countries.values():
            if hasattr(country, 'decay_all_memories'):
                country.decay_all_memories(months_passed)

        for country in world.tier4_countries.values():
            if hasattr(country, 'memory_scores'):
                for memory in country.memory_scores.values():
                    memory.decay(months_passed)
