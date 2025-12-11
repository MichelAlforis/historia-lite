"""
RippleEffectEngine for Historia Lite - Timeline Backbone

Manages cascade effects when events trigger chain reactions.
Implements the "ripple" system where events propagate through:
- Geographical proximity (neighbors feel effects)
- Alliance networks (allies react)
- Economic ties (trade partners affected)
- Power balance (superpowers respond to threats)
"""
import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .world import GameDate, World
from .timeline import TimelineManager, TimelineEvent, EventType, EventSource, EventFamily, CausalLink

logger = logging.getLogger(__name__)


class RippleRule(BaseModel):
    """Defines how an event type ripples to other countries"""
    event_type: str
    spread_to_neighbors: bool = True
    spread_to_allies: bool = True
    spread_to_rivals: bool = False
    spread_to_bloc: bool = True
    base_decay: float = 0.5  # How much effect decays per hop
    max_hops: int = 2  # Maximum propagation distance
    min_importance: int = 3  # Minimum importance to trigger ripple


class RippleEffect(BaseModel):
    """A single ripple effect to be applied"""
    target_country: str
    source_event_id: str
    effects: Dict[str, float]  # stat -> delta
    delay_months: int = 0
    strength: float = 1.0
    description: str = ""
    description_fr: str = ""


class RippleEffectEngine:
    """
    Engine for calculating and applying cascade effects.

    When a significant event occurs, it can:
    1. Affect neighboring countries (geographic ripple)
    2. Trigger reactions from allies/rivals
    3. Cause economic spillover
    4. Shift power balance perceptions
    """

    def __init__(self):
        self.rules = self._init_default_rules()
        self.pending_ripples: List[RippleEffect] = []

    def _init_default_rules(self) -> Dict[str, RippleRule]:
        """Initialize default ripple rules by event type"""
        return {
            "war": RippleRule(
                event_type="war",
                spread_to_neighbors=True,
                spread_to_allies=True,
                spread_to_rivals=True,
                spread_to_bloc=True,
                base_decay=0.6,
                max_hops=3,
                min_importance=2
            ),
            "military": RippleRule(
                event_type="military",
                spread_to_neighbors=True,
                spread_to_allies=True,
                spread_to_rivals=True,
                spread_to_bloc=False,
                base_decay=0.5,
                max_hops=2,
                min_importance=3
            ),
            "economic": RippleRule(
                event_type="economic",
                spread_to_neighbors=True,
                spread_to_allies=False,
                spread_to_bloc=True,
                base_decay=0.4,
                max_hops=2,
                min_importance=3
            ),
            "diplomatic": RippleRule(
                event_type="diplomatic",
                spread_to_neighbors=False,
                spread_to_allies=True,
                spread_to_bloc=True,
                base_decay=0.3,
                max_hops=1,
                min_importance=4
            ),
            "crisis": RippleRule(
                event_type="crisis",
                spread_to_neighbors=True,
                spread_to_allies=True,
                spread_to_rivals=True,
                spread_to_bloc=True,
                base_decay=0.7,
                max_hops=3,
                min_importance=2
            ),
            "political": RippleRule(
                event_type="political",
                spread_to_neighbors=True,
                spread_to_allies=False,
                spread_to_bloc=False,
                base_decay=0.3,
                max_hops=1,
                min_importance=4
            )
        }

    def calculate_ripples(
        self,
        event: TimelineEvent,
        world: World,
        timeline: TimelineManager
    ) -> List[RippleEffect]:
        """
        Calculate all ripple effects from an event.
        Returns list of effects to be applied (some immediate, some delayed).
        """
        ripples = []

        event_type = event.type if isinstance(event.type, str) else event.type.value
        rule = self.rules.get(event_type, self.rules.get("political"))

        if event.importance < rule.min_importance:
            return ripples

        # Get affected countries
        affected = self._get_affected_countries(event, world, rule)

        for country_id, hop_distance, relationship in affected:
            strength = rule.base_decay ** hop_distance
            effects = self._calculate_country_effects(event, country_id, relationship, strength, world)

            if effects:
                delay = self._calculate_delay(hop_distance, event_type)
                ripple = RippleEffect(
                    target_country=country_id,
                    source_event_id=event.id,
                    effects=effects,
                    delay_months=delay,
                    strength=strength,
                    description=f"Ripple effect from {event.title}",
                    description_fr=f"Effet cascade de {event.title_fr}"
                )
                ripples.append(ripple)

                # Track ripple targets on the event
                if country_id not in event.ripple_targets:
                    event.ripple_targets.append(country_id)

        return ripples

    def _get_affected_countries(
        self,
        event: TimelineEvent,
        world: World,
        rule: RippleRule
    ) -> List[Tuple[str, int, str]]:
        """
        Get list of countries affected by ripple.
        Returns: [(country_id, hop_distance, relationship_type), ...]
        """
        affected = []
        actor = world.get_any_country(event.actor_country)

        if not actor:
            return affected

        # Direct targets are hop 0
        for target_id in event.target_countries:
            affected.append((target_id, 0, "target"))

        # Neighbors (hop 1)
        if rule.spread_to_neighbors and hasattr(actor, 'neighbors'):
            for neighbor_id in getattr(actor, 'neighbors', []):
                if neighbor_id not in event.target_countries:
                    affected.append((neighbor_id, 1, "neighbor"))

        # For Tier 1-3 countries
        if hasattr(actor, 'blocs'):
            # Allies (hop 1)
            if rule.spread_to_allies and hasattr(actor, 'allies'):
                for ally_id in actor.allies:
                    if ally_id not in [a[0] for a in affected]:
                        affected.append((ally_id, 1, "ally"))

            # Bloc members (hop 1-2)
            if rule.spread_to_bloc:
                for bloc in actor.blocs:
                    bloc_members = world.get_bloc_members(bloc)
                    for member in bloc_members:
                        if member.id not in [a[0] for a in affected] and member.id != actor.id:
                            affected.append((member.id, 2, "bloc_member"))

            # Rivals (hop 1)
            if rule.spread_to_rivals and hasattr(actor, 'rivals'):
                for rival_id in actor.rivals:
                    if rival_id not in [a[0] for a in affected]:
                        affected.append((rival_id, 1, "rival"))

        # Limit to max_hops
        affected = [(c, h, r) for c, h, r in affected if h <= rule.max_hops]

        return affected

    def _calculate_country_effects(
        self,
        event: TimelineEvent,
        country_id: str,
        relationship: str,
        strength: float,
        world: World
    ) -> Dict[str, float]:
        """Calculate specific effects on a country based on relationship"""
        effects = {}
        event_type = event.type if isinstance(event.type, str) else event.type.value
        base_magnitude = event.importance * strength

        # Neighbors feel stability/economic effects
        if relationship == "neighbor":
            if event_type in ("war", "crisis"):
                effects["stability"] = -base_magnitude * 0.5
                effects["economy"] = -base_magnitude * 0.3
            elif event_type == "economic":
                effects["economy"] = base_magnitude * 0.2 * (-1 if not self._is_positive_event(event) else 1)

        # Allies share positive/negative fortune
        elif relationship == "ally":
            if event_type in ("war", "military"):
                effects["stability"] = -base_magnitude * 0.3
            elif event_type == "diplomatic":
                effects["soft_power"] = base_magnitude * 0.2

        # Rivals get opposite effects
        elif relationship == "rival":
            if event_type in ("war", "crisis"):
                # Rival's enemy weakened = rival gains
                effects["stability"] = base_magnitude * 0.2
            elif event_type == "economic":
                # Economic problems for enemy = opportunity
                if not self._is_positive_event(event):
                    effects["economy"] = base_magnitude * 0.1

        # Bloc members share some effects
        elif relationship == "bloc_member":
            if event_type == "economic":
                effects["economy"] = base_magnitude * 0.15 * (-1 if not self._is_positive_event(event) else 1)
            elif event_type == "diplomatic":
                effects["soft_power"] = base_magnitude * 0.1

        # Direct targets get full effects from event
        elif relationship == "target":
            # Use event's defined effects for targets
            if country_id in event.effects:
                return event.effects[country_id]

        return {k: round(v, 2) for k, v in effects.items() if abs(v) >= 0.1}

    def _calculate_delay(self, hop_distance: int, event_type: str) -> int:
        """Calculate how many months delay before ripple takes effect"""
        base_delay = hop_distance

        # Some event types propagate faster
        if event_type in ("war", "crisis"):
            return max(0, base_delay - 1)
        elif event_type == "economic":
            return base_delay + 1

        return base_delay

    def _is_positive_event(self, event: TimelineEvent) -> bool:
        """Check if event is generally positive"""
        negative_keywords = ["sanction", "attack", "war", "crisis", "collapse", "embargo"]
        title_lower = event.title.lower()
        return not any(kw in title_lower for kw in negative_keywords)

    def apply_immediate_ripples(
        self,
        ripples: List[RippleEffect],
        world: World
    ) -> List[RippleEffect]:
        """Apply ripples with no delay, return delayed ones"""
        delayed = []

        for ripple in ripples:
            if ripple.delay_months == 0:
                self._apply_ripple_to_country(ripple, world)
            else:
                delayed.append(ripple)

        return delayed

    def _apply_ripple_to_country(self, ripple: RippleEffect, world: World) -> None:
        """Apply a ripple effect to a country"""
        country = world.get_any_country(ripple.target_country)
        if not country:
            return

        for stat, delta in ripple.effects.items():
            if hasattr(country, stat):
                current = getattr(country, stat)
                if isinstance(current, (int, float)):
                    new_value = max(0, min(100, current + delta))
                    setattr(country, stat, int(new_value) if isinstance(current, int) else new_value)
                    logger.debug(f"Ripple: {ripple.target_country}.{stat} {current} -> {new_value}")

    def process_pending_ripples(self, world: World, months_passed: int = 1) -> List[RippleEffect]:
        """Process pending ripples, apply those that are ready"""
        applied = []
        still_pending = []

        for ripple in self.pending_ripples:
            ripple.delay_months -= months_passed
            if ripple.delay_months <= 0:
                self._apply_ripple_to_country(ripple, world)
                applied.append(ripple)
            else:
                still_pending.append(ripple)

        self.pending_ripples = still_pending
        return applied

    def add_pending_ripples(self, ripples: List[RippleEffect]) -> None:
        """Add ripples to pending queue"""
        self.pending_ripples.extend(ripples)

    def generate_ripple_event(
        self,
        source_event: TimelineEvent,
        ripple: RippleEffect,
        current_date: GameDate,
        timeline: TimelineManager
    ) -> Optional[TimelineEvent]:
        """
        Generate a timeline event representing a ripple effect.
        Creates narrative continuity by linking to source.
        """
        if ripple.strength < 0.3:
            return None  # Too weak to warrant an event

        # Generate narrative description
        title = f"Ripple: {ripple.target_country} affected by {source_event.actor_country} events"
        title_fr = f"Cascade: {ripple.target_country} affecté par les événements de {source_event.actor_country}"

        description = f"As a consequence of {source_event.title}, {ripple.target_country} experiences indirect effects."
        description_fr = f"Suite à {source_event.title_fr}, {ripple.target_country} subit des effets indirects."

        event = TimelineEvent(
            id=timeline.generate_event_id("rpl"),
            date=current_date,
            actor_country=ripple.target_country,
            target_countries=[source_event.actor_country],
            title=title,
            title_fr=title_fr,
            description=description,
            description_fr=description_fr,
            type=EventType.POLITICAL,
            source=EventSource.SYSTEM,
            importance=max(1, int(source_event.importance * ripple.strength)),
            family=EventFamily.ESCALATION,
            effects={ripple.target_country: ripple.effects},
            caused_by=source_event.id,
            causal_chain_depth=source_event.causal_chain_depth + 1,
            ripple_weight=ripple.strength * 0.5  # Reduced for secondary ripples
        )

        # Link to source
        timeline.link_events(source_event.id, event.id, ripple.strength)

        return event

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            "pending_ripples": [r.model_dump() for r in self.pending_ripples]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RippleEffectEngine":
        """Deserialize from storage"""
        engine = cls()
        engine.pending_ripples = [
            RippleEffect(**r) for r in data.get("pending_ripples", [])
        ]
        return engine
