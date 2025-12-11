"""Crisis Management System for Historia Lite - Phase 2 Axes 4-5

Implements:
- CrisisArc: Dramatic arc structure for crises (latent -> escalation -> climax -> resolution -> aftermath)
- CrisisManager: Manages up to 4 active crises simultaneously
- Living Crises: Crises as entities with momentum, media attention, spillover risk
"""
import logging
import random
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .world import World, GameDate
    from .timeline import TimelineManager, TimelineEvent

logger = logging.getLogger(__name__)


class CrisisPhase(str, Enum):
    """The 5 phases of a crisis arc - like a TV series story arc"""
    LATENT = "latent"           # Underlying tensions, weak signals
    ESCALATION = "escalation"   # Rising tensions, incidents
    CLIMAX = "climax"           # Breaking point, critical moment
    RESOLUTION = "resolution"   # Denouement (war, agreement, or freeze)
    AFTERMATH = "aftermath"     # Post-crisis consequences


# Phase display names
PHASE_NAMES_FR = {
    CrisisPhase.LATENT: "Latente",
    CrisisPhase.ESCALATION: "Escalade",
    CrisisPhase.CLIMAX: "Climax",
    CrisisPhase.RESOLUTION: "Resolution",
    CrisisPhase.AFTERMATH: "Apres-crise",
}

PHASE_NAMES_EN = {
    CrisisPhase.LATENT: "Latent",
    CrisisPhase.ESCALATION: "Escalation",
    CrisisPhase.CLIMAX: "Climax",
    CrisisPhase.RESOLUTION: "Resolution",
    CrisisPhase.AFTERMATH: "Aftermath",
}


class CrisisOutcome(str, Enum):
    """Possible outcomes for a crisis"""
    WAR = "war"                 # Open conflict
    TREATY = "treaty"           # Diplomatic resolution
    FROZEN = "frozen"           # Stalemate, unresolved
    COLLAPSE = "collapse"       # One side collapses
    ESCALATION = "escalation"   # Escalates to larger conflict
    UNKNOWN = "unknown"         # Still unresolved


class PhaseHistoryEntry(BaseModel):
    """Record of a phase transition"""
    phase: CrisisPhase
    start_year: int
    start_month: int
    end_year: Optional[int] = None
    end_month: Optional[int] = None
    key_events: List[str] = Field(default_factory=list)  # Event IDs


class CrisisArc(BaseModel):
    """
    Dramatic arc of a geopolitical crisis.
    Each crisis follows a 5-phase structure like a TV series story arc.
    """

    id: str
    name: str
    name_fr: str

    # Main actors
    primary_actors: List[str] = Field(default_factory=list)    # Main countries involved
    secondary_actors: List[str] = Field(default_factory=list)  # Peripheral countries

    # Current state
    current_phase: CrisisPhase = CrisisPhase.LATENT
    phase_start_year: int = 2025
    phase_start_month: int = 1
    intensity: int = 0             # 0-100, rises with escalation

    # Phase history
    phase_history: List[PhaseHistoryEntry] = Field(default_factory=list)

    # Linked events
    events: List[str] = Field(default_factory=list)  # Event IDs

    # Transition probabilities
    escalation_probability: float = 0.3
    resolution_probability: float = 0.1

    # Potential outcome
    possible_outcomes: List[str] = Field(default_factory=lambda: ["war", "treaty", "frozen"])
    outcome: CrisisOutcome = CrisisOutcome.UNKNOWN

    # Narrative metadata
    root_causes: List[str] = Field(default_factory=list)    # Deep causes
    proximate_causes: List[str] = Field(default_factory=list)  # Immediate causes
    flash_point: Optional[str] = None  # Triggering event ID

    # === LIVING CRISIS ATTRIBUTES (Axe 5) ===

    # "Vital signs"
    momentum: int = 0              # -100 (declining) to +100 (expanding)
    media_attention: int = 50      # Media coverage (0-100)
    international_involvement: int = 0  # Number of indirectly involved countries

    # Causal analysis
    deep_causes: List[str] = Field(default_factory=list)    # Structural causes
    immediate_triggers: List[str] = Field(default_factory=list)  # Proximate causes

    # AI predictions
    ai_predicted_outcome: Optional[str] = None
    ai_confidence: float = 0.5

    # Inter-crisis dynamics
    linked_crises: List[str] = Field(default_factory=list)  # IDs of linked crises
    spillover_risk: float = 0.0    # Risk of contamination to other regions

    # Timing
    created_year: int = 2025
    created_month: int = 1
    months_active: int = 0

    class Config:
        use_enum_values = True

    def get_phase_display(self, lang: str = "fr") -> str:
        """Get display name for current phase"""
        phase_enum = CrisisPhase(self.current_phase) if isinstance(self.current_phase, str) else self.current_phase
        if lang == "fr":
            return PHASE_NAMES_FR.get(phase_enum, self.current_phase)
        return PHASE_NAMES_EN.get(phase_enum, self.current_phase)

    def add_event(self, event_id: str) -> None:
        """Add an event to this crisis"""
        if event_id not in self.events:
            self.events.append(event_id)

    def get_phase_progress(self) -> float:
        """Get progress through the crisis arc (0.0 to 1.0)"""
        phase_order = [CrisisPhase.LATENT, CrisisPhase.ESCALATION, CrisisPhase.CLIMAX,
                       CrisisPhase.RESOLUTION, CrisisPhase.AFTERMATH]
        current = CrisisPhase(self.current_phase) if isinstance(self.current_phase, str) else self.current_phase
        try:
            idx = phase_order.index(current)
            return idx / (len(phase_order) - 1)
        except ValueError:
            return 0.0

    def is_active(self) -> bool:
        """Check if crisis is still active"""
        current = CrisisPhase(self.current_phase) if isinstance(self.current_phase, str) else self.current_phase
        return current not in [CrisisPhase.AFTERMATH]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API/frontend"""
        return {
            "id": self.id,
            "name": self.name,
            "name_fr": self.name_fr,
            "primary_actors": self.primary_actors,
            "secondary_actors": self.secondary_actors,
            "current_phase": self.current_phase,
            "phase_display_fr": self.get_phase_display("fr"),
            "phase_display_en": self.get_phase_display("en"),
            "phase_progress": self.get_phase_progress(),
            "intensity": self.intensity,
            "momentum": self.momentum,
            "media_attention": self.media_attention,
            "international_involvement": self.international_involvement,
            "months_active": self.months_active,
            "event_count": len(self.events),
            "outcome": self.outcome,
            "spillover_risk": self.spillover_risk,
            "ai_predicted_outcome": self.ai_predicted_outcome,
            "ai_confidence": self.ai_confidence,
            "is_active": self.is_active(),
        }


class CrisisManager:
    """
    Manages active crises (max 4 simultaneous).
    Handles phase transitions, crisis lifecycle, and cross-crisis dynamics.
    """

    MAX_ACTIVE_CRISES = 4

    def __init__(self):
        self.active_crises: List[CrisisArc] = []
        self.resolved_crises: List[CrisisArc] = []
        self._crisis_id_counter: int = 0

    def generate_crisis_id(self) -> str:
        """Generate a unique crisis ID"""
        self._crisis_id_counter += 1
        return f"crisis_{self._crisis_id_counter}"

    def create_crisis(
        self,
        name: str,
        name_fr: str,
        actors: List[str],
        trigger_event_id: Optional[str] = None,
        current_year: int = 2025,
        current_month: int = 1,
        root_causes: Optional[List[str]] = None
    ) -> Optional[CrisisArc]:
        """Create a new crisis if slot available"""

        # Check if a similar crisis already exists
        for crisis in self.active_crises:
            if any(a in crisis.primary_actors for a in actors):
                logger.debug(f"Crisis already exists involving {actors}")
                return None

        # Close weakest crisis if at max
        if len(self.active_crises) >= self.MAX_ACTIVE_CRISES:
            self._close_weakest_crisis()

        crisis = CrisisArc(
            id=self.generate_crisis_id(),
            name=name,
            name_fr=name_fr,
            primary_actors=actors,
            flash_point=trigger_event_id,
            created_year=current_year,
            created_month=current_month,
            phase_start_year=current_year,
            phase_start_month=current_month,
            root_causes=root_causes or [],
        )

        # Initial phase history
        crisis.phase_history.append(PhaseHistoryEntry(
            phase=CrisisPhase.LATENT,
            start_year=current_year,
            start_month=current_month,
            key_events=[trigger_event_id] if trigger_event_id else []
        ))

        self.active_crises.append(crisis)
        logger.info(f"Crisis created: {name_fr} involving {actors}")
        return crisis

    def _close_weakest_crisis(self) -> None:
        """Close the weakest/oldest crisis to make room"""
        if not self.active_crises:
            return

        # Sort by intensity (weakest first), then by age (oldest first)
        self.active_crises.sort(key=lambda c: (c.intensity, -c.months_active))
        closed = self.active_crises.pop(0)
        closed.outcome = CrisisOutcome.FROZEN
        self.resolved_crises.append(closed)
        logger.info(f"Crisis closed (frozen): {closed.name_fr}")

    def get_crisis_by_id(self, crisis_id: str) -> Optional[CrisisArc]:
        """Get a crisis by ID"""
        for crisis in self.active_crises:
            if crisis.id == crisis_id:
                return crisis
        for crisis in self.resolved_crises:
            if crisis.id == crisis_id:
                return crisis
        return None

    def get_crisis_for_countries(self, countries: List[str]) -> Optional[CrisisArc]:
        """Find an active crisis involving any of these countries"""
        for crisis in self.active_crises:
            if any(c in crisis.primary_actors or c in crisis.secondary_actors for c in countries):
                return crisis
        return None

    def add_event_to_crisis(self, crisis_id: str, event_id: str) -> bool:
        """Add an event to a crisis"""
        crisis = self.get_crisis_by_id(crisis_id)
        if crisis:
            crisis.add_event(event_id)
            return True
        return False

    def process_monthly(
        self,
        world: "World",
        timeline: Optional["TimelineManager"] = None
    ) -> List[str]:
        """
        Process all active crises for the month.
        Updates vitals, checks phase transitions, handles outcomes.
        """
        messages = []
        to_resolve = []

        for crisis in self.active_crises:
            crisis.months_active += 1

            # Update vital signs
            self._update_crisis_vitals(crisis, world, timeline)

            # Check phase transition
            new_phase = self._check_phase_transition(crisis, world, timeline)
            if new_phase:
                old_phase = crisis.current_phase
                self._transition_phase(crisis, new_phase, world.year, world.month)
                messages.append(
                    f"Crise '{crisis.name_fr}': passage de {PHASE_NAMES_FR.get(CrisisPhase(old_phase), old_phase)} "
                    f"a {PHASE_NAMES_FR.get(new_phase, new_phase)}"
                )

            # Check if crisis is resolved
            if not crisis.is_active():
                to_resolve.append(crisis)
                messages.append(f"Crise '{crisis.name_fr}' resolue: {crisis.outcome}")

        # Move resolved crises
        for crisis in to_resolve:
            self.active_crises.remove(crisis)
            self.resolved_crises.append(crisis)

        return messages

    def _update_crisis_vitals(
        self,
        crisis: CrisisArc,
        world: "World",
        timeline: Optional["TimelineManager"]
    ) -> None:
        """Update the vital signs of a crisis"""

        # Get recent events for this crisis
        recent_event_count = 0
        escalation_events = 0
        deescalation_events = 0

        if timeline:
            # Count events in last month involving crisis actors
            month_events = timeline.get_events_for_month(world.year, world.month)
            for event in month_events:
                if (event.actor_country in crisis.primary_actors or
                    any(t in crisis.primary_actors for t in event.target_countries)):

                    recent_event_count += 1
                    crisis.add_event(event.id)

                    # Categorize by family/type
                    family = getattr(event, 'family', 'tactical')
                    if family == "escalation" or event.type in ["war", "military", "crisis"]:
                        escalation_events += 1
                    elif family in ["opportunity", "diplomatic"] or event.type == "diplomatic":
                        deescalation_events += 1

        # Update momentum
        momentum_delta = (escalation_events - deescalation_events) * 15
        crisis.momentum = max(-100, min(100, crisis.momentum + momentum_delta))

        # Update intensity based on momentum
        if crisis.momentum > 20:
            crisis.intensity = min(100, crisis.intensity + 5)
        elif crisis.momentum < -20:
            crisis.intensity = max(0, crisis.intensity - 3)

        # Update media attention
        if recent_event_count > 0:
            crisis.media_attention = min(100, crisis.media_attention + recent_event_count * 8)
        else:
            crisis.media_attention = max(0, crisis.media_attention - 5)

        # Update international involvement
        involved = set(crisis.primary_actors + crisis.secondary_actors)
        if timeline:
            for event_id in crisis.events[-20:]:  # Last 20 events
                event = timeline.get_event_by_id(event_id)
                if event:
                    involved.add(event.actor_country)
                    involved.update(event.target_countries)
        crisis.international_involvement = len(involved)

        # Update spillover risk based on intensity and involvement
        crisis.spillover_risk = min(1.0, (crisis.intensity / 100) * (crisis.international_involvement / 10))

    def _check_phase_transition(
        self,
        crisis: CrisisArc,
        world: "World",
        timeline: Optional["TimelineManager"]
    ) -> Optional[CrisisPhase]:
        """Check if a crisis should transition to a new phase"""

        current = CrisisPhase(crisis.current_phase) if isinstance(crisis.current_phase, str) else crisis.current_phase

        if current == CrisisPhase.LATENT:
            # Transition to ESCALATION if intensity > 40 or major incident
            if crisis.intensity > 40 or crisis.momentum > 50:
                return CrisisPhase.ESCALATION

        elif current == CrisisPhase.ESCALATION:
            # Transition to CLIMAX if critical event (importance 5) or very high intensity
            if crisis.intensity > 75:
                return CrisisPhase.CLIMAX

            # Check for critical events
            if timeline:
                recent = timeline.get_events_for_month(world.year, world.month)
                for event in recent:
                    if event.importance >= 5:
                        if (event.actor_country in crisis.primary_actors or
                            any(t in crisis.primary_actors for t in event.target_countries)):
                            return CrisisPhase.CLIMAX

            # Return to LATENT if tensions drop significantly
            if crisis.intensity < 20 and crisis.momentum < -30:
                return CrisisPhase.LATENT

        elif current == CrisisPhase.CLIMAX:
            # Must resolve within 3 months max
            months_in_phase = self._months_in_current_phase(crisis, world)
            if months_in_phase >= 3:
                return CrisisPhase.RESOLUTION

            # Or if intensity drops dramatically
            if crisis.intensity < 30:
                return CrisisPhase.RESOLUTION

        elif current == CrisisPhase.RESOLUTION:
            # Transition to AFTERMATH after resolution
            months_in_phase = self._months_in_current_phase(crisis, world)
            if months_in_phase >= 2 or crisis.intensity < 10:
                # Determine outcome
                self._determine_outcome(crisis, world)
                return CrisisPhase.AFTERMATH

        return None

    def _months_in_current_phase(self, crisis: CrisisArc, world: "World") -> int:
        """Calculate months spent in current phase"""
        start_months = crisis.phase_start_year * 12 + crisis.phase_start_month
        current_months = world.year * 12 + world.month
        return current_months - start_months

    def _transition_phase(
        self,
        crisis: CrisisArc,
        new_phase: CrisisPhase,
        year: int,
        month: int
    ) -> None:
        """Transition a crisis to a new phase"""

        # Close current phase in history
        if crisis.phase_history:
            crisis.phase_history[-1].end_year = year
            crisis.phase_history[-1].end_month = month

        # Update current phase
        old_phase = crisis.current_phase
        crisis.current_phase = new_phase
        crisis.phase_start_year = year
        crisis.phase_start_month = month

        # Add new phase to history
        crisis.phase_history.append(PhaseHistoryEntry(
            phase=new_phase,
            start_year=year,
            start_month=month
        ))

        logger.info(f"Crisis {crisis.name_fr}: {old_phase} -> {new_phase}")

    def _determine_outcome(self, crisis: CrisisArc, world: "World") -> None:
        """Determine the outcome of a crisis based on its history"""

        # Check for active conflicts between actors
        has_war = False
        if hasattr(world, 'active_conflicts'):
            for conflict in world.active_conflicts:
                if any(a in crisis.primary_actors for a in conflict.attackers + conflict.defenders):
                    has_war = True
                    break

        if has_war:
            crisis.outcome = CrisisOutcome.WAR
        elif crisis.momentum < -50:
            # Diplomatic resolution if momentum strongly negative
            crisis.outcome = CrisisOutcome.TREATY
        elif crisis.intensity < 20:
            # Collapse if intensity very low
            crisis.outcome = CrisisOutcome.COLLAPSE
        else:
            # Default to frozen conflict
            crisis.outcome = CrisisOutcome.FROZEN

    def get_active_summary(self) -> List[Dict[str, Any]]:
        """Get summary of active crises for UI"""
        return [crisis.to_dict() for crisis in self.active_crises]

    def get_crisis_involving_player(self, player_country_id: str) -> List[CrisisArc]:
        """Get crises involving the player's country"""
        result = []
        for crisis in self.active_crises:
            if (player_country_id in crisis.primary_actors or
                player_country_id in crisis.secondary_actors):
                result.append(crisis)
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            "active_crises": [c.model_dump() for c in self.active_crises],
            "resolved_crises": [c.model_dump() for c in self.resolved_crises[-10:]],  # Keep last 10
            "crisis_id_counter": self._crisis_id_counter
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrisisManager":
        """Deserialize from storage"""
        manager = cls()
        manager.active_crises = [CrisisArc(**c) for c in data.get("active_crises", [])]
        manager.resolved_crises = [CrisisArc(**c) for c in data.get("resolved_crises", [])]
        manager._crisis_id_counter = data.get("crisis_id_counter", 0)
        return manager


# =============================================================================
# CRISIS DETECTION - Auto-detect crisis-worthy situations
# =============================================================================

def detect_potential_crisis(
    event: "TimelineEvent",
    world: "World",
    crisis_manager: CrisisManager
) -> Optional[CrisisArc]:
    """
    Detect if an event should trigger a new crisis.
    Returns the created crisis or None.
    """

    # Only high-importance events can trigger crises
    if event.importance < 4:
        return None

    # Check if crisis already exists for these actors
    actors = [event.actor_country] + event.target_countries
    existing = crisis_manager.get_crisis_for_countries(actors)
    if existing:
        # Add event to existing crisis instead
        existing.add_event(event.id)
        return None

    # Crisis-worthy event types
    crisis_types = ["war", "military", "crisis"]
    event_type = event.type if isinstance(event.type, str) else event.type.value

    if event_type in crisis_types and event.importance >= 4:
        # Generate crisis name from event
        name = f"{event.actor_country}-{event.target_countries[0] if event.target_countries else 'Region'} Crisis"
        name_fr = f"Crise {event.actor_country}-{event.target_countries[0] if event.target_countries else 'regionale'}"

        crisis = crisis_manager.create_crisis(
            name=name,
            name_fr=name_fr,
            actors=actors,
            trigger_event_id=event.id,
            current_year=event.date.year,
            current_month=event.date.month,
            root_causes=[event.title_fr]
        )

        if crisis:
            # Set initial intensity based on event importance
            crisis.intensity = event.importance * 15
            logger.info(f"Auto-detected crisis: {name_fr}")

        return crisis

    return None
