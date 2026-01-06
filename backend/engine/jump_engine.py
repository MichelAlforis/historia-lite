"""Jump Engine for Historia Narrative (PaxHistoria-style)

The Jump Forward mechanic is the core of PaxHistoria gameplay:
1. Player accumulates actions in queue
2. Player clicks "Jump Forward" (>>> button)
3. Engine resolves all actions (player + adversary)
4. Events are generated with causality
5. Player reads events one by one (Save/Intervene)

This engine handles step 3-4: resolution and event generation.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .narrative_state import NarrativeWorldState, GamePhase
from .action_queue import ActionQueue, QueuedAction
from .adversary_ai import AdversaryAI, AIAction

logger = logging.getLogger(__name__)


# =============================================================================
# JUMP DURATION
# =============================================================================

class JumpDuration(str, Enum):
    """Duration options for Jump Forward"""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    NEXT_EVENT = "next_event"


DURATION_MONTHS = {
    JumpDuration.WEEK: 0,      # Less than a month
    JumpDuration.MONTH: 1,
    JumpDuration.QUARTER: 3,
    JumpDuration.YEAR: 12,
    JumpDuration.NEXT_EVENT: 1,  # Variable, default to 1
}


# =============================================================================
# EVENT TYPES
# =============================================================================

class JumpEventType(str, Enum):
    """Types of events generated during jump"""
    PLAYER_ACTION = "player_action"
    ADVERSARY_ACTION = "adversary_action"
    WORLD_EVENT = "world_event"
    CRISIS = "crisis"
    RESOLUTION = "resolution"
    TIME_PASSAGE = "time_passage"
    CONSEQUENCE = "consequence"


class JumpEvent(BaseModel):
    """Event generated during Jump Forward"""
    id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    type: JumpEventType
    category: str = ""  # DIPLO, MIL, COV, etc.

    # Display
    title_fr: str
    description_fr: str
    title_en: str = ""
    description_en: str = ""

    # Context
    target_zone: Optional[str] = None
    target_actor: Optional[str] = None
    source: str = ""  # player, adversary, world

    # Effects applied
    effects: Dict[str, Any] = Field(default_factory=dict)

    # Importance
    importance: str = "normal"  # minor, normal, major, critical
    risk_level: str = "low"

    # Causality
    caused_by: Optional[str] = None  # ID of causing event/action
    triggers: List[str] = Field(default_factory=list)  # IDs of triggered events

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON"""
        return {
            "id": self.id,
            "type": self.type.value,
            "category": self.category,
            "title_fr": self.title_fr,
            "description_fr": self.description_fr,
            "title_en": self.title_en,
            "description_en": self.description_en,
            "target_zone": self.target_zone,
            "target_actor": self.target_actor,
            "source": self.source,
            "effects": self.effects,
            "importance": self.importance,
            "risk_level": self.risk_level,
            "caused_by": self.caused_by,
            "triggers": self.triggers,
        }


# =============================================================================
# JUMP ENGINE
# =============================================================================

class JumpEngine:
    """Engine for resolving Jump Forward"""

    def __init__(self, adversary_ai: AdversaryAI):
        self.adversary_ai = adversary_ai

    async def execute_jump(
        self,
        state: NarrativeWorldState,
        duration: str
    ) -> List[JumpEvent]:
        """Execute Jump Forward and generate events

        Main entry point for jump resolution.
        """
        events: List[JumpEvent] = []

        # 1. Get player actions from queue
        queue = state.get_action_queue()
        player_actions = queue.get_active_actions()

        # 2. Get adversary actions (should already be planned)
        adversary_results = await self.adversary_ai.execute_planned_actions(state)

        # 3. Resolve player actions
        for action in player_actions:
            event = self._resolve_player_action(action, state)
            events.append(event)

        # 4. Add adversary action events
        for result in adversary_results:
            action_data = result["action"]
            if action_data.get("visible_to_player", True):
                event = self._create_adversary_event(action_data, result["result"])
                events.append(event)

        # 5. Check for triggered events (consequences, crises)
        triggered = self._check_triggered_events(state, events)
        events.extend(triggered)

        # 6. Advance time
        months = DURATION_MONTHS.get(JumpDuration(duration), 1)
        time_event = self._advance_time(state, months, duration)
        events.append(time_event)

        # 7. Check world events (based on tensions, stability)
        world_events = self._generate_world_events(state)
        events.extend(world_events)

        # 8. Order events by importance and causality
        events = self._order_events(events)

        logger.info(f"Jump executed: {len(events)} events generated")
        return events

    def _resolve_player_action(
        self,
        action: QueuedAction,
        state: NarrativeWorldState
    ) -> JumpEvent:
        """Resolve a single player action"""
        # Spend political capital
        state.player.spend_capital(action.political_cost)

        # Apply effects based on action type
        effects_applied = {}

        if action.target_zone and action.target_zone in state.zones:
            zone = state.zones[action.target_zone]

            # Apply predicted effects
            for effect_key, value in action.predicted_effects.items():
                if effect_key == "influence_us":
                    zone.influence_us = max(0, min(100, zone.influence_us + value))
                    effects_applied["influence_us"] = value
                elif effect_key == "control_us":
                    zone.control_us = max(0, min(100, zone.control_us + value))
                    effects_applied["control_us"] = value
                elif effect_key == "stability":
                    zone.stability = max(0, min(100, zone.stability + value))
                    effects_applied["stability"] = value
                elif effect_key == "world_tension":
                    state.world_tension = max(0, min(100, state.world_tension + value))
                    effects_applied["world_tension"] = value
                elif effect_key == "defcon":
                    state.defcon = max(1, min(5, state.defcon + value))
                    effects_applied["defcon"] = value

        # Apply standard effects based on action type
        if "MIL_REINFORCE" in action.intention_type:
            if action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.control_us = min(100, zone.control_us + 15)
                    zone.influence_us = min(100, zone.influence_us + 5)
                    effects_applied["control_us"] = effects_applied.get("control_us", 0) + 15

        elif "COV_DESTAB" in action.intention_type:
            if action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.stability = max(0, zone.stability - 15)
                    zone.influence_ussr = max(0, zone.influence_ussr - 10)
                    effects_applied["stability"] = effects_applied.get("stability", 0) - 15

        # Determine importance
        importance = "normal"
        if action.risk_level in ["high", "extreme"]:
            importance = "major"
        if "NUCLEAR" in action.intention_type or "BLOCKADE" in action.intention_type:
            importance = "critical"

        return JumpEvent(
            type=JumpEventType.PLAYER_ACTION,
            category=action.intention_type.split("_")[0],
            title_fr=action.description_fr,
            description_fr=f"Vous avez execute: {action.description_fr}",
            target_zone=action.target_zone,
            target_actor=action.target_actor,
            source="player",
            effects=effects_applied,
            importance=importance,
            risk_level=action.risk_level,
        )

    def _create_adversary_event(
        self,
        action_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> JumpEvent:
        """Create event from adversary action"""
        action_type = action_data.get("action_type", "unknown")
        category = action_type.split("_")[0] if "_" in action_type else "USSR"

        importance = "normal"
        if "military" in action_type.lower() or "nuclear" in action_type.lower():
            importance = "major"
        if "threaten" in action_type.lower():
            importance = "major"

        return JumpEvent(
            type=JumpEventType.ADVERSARY_ACTION,
            category=category,
            title_fr=action_data.get("reason_fr", "Action sovietique"),
            description_fr=f"L'URSS a agi: {action_data.get('reason_fr', 'Action inconnue')}",
            target_zone=action_data.get("target_zone"),
            target_actor=action_data.get("target_country"),
            source="adversary",
            effects=result.get("changes", {}),
            importance=importance,
        )

    def _check_triggered_events(
        self,
        state: NarrativeWorldState,
        existing_events: List[JumpEvent]
    ) -> List[JumpEvent]:
        """Check for events triggered by actions"""
        triggered = []

        # Check each zone for consequences
        for zone_id, zone in state.zones.items():
            # Crisis trigger: stability very low
            if zone.stability < 25 and not zone.has_crisis:
                zone.has_crisis = True
                zone.crisis_type = "instability"
                triggered.append(JumpEvent(
                    type=JumpEventType.CRISIS,
                    category="CRISIS",
                    title_fr=f"Crise en {zone.name_fr}",
                    description_fr=f"L'instabilite en {zone.name_fr} atteint un point critique. Une crise eclate.",
                    target_zone=zone_id,
                    source="world",
                    importance="major",
                    effects={"stability": -10},
                ))

            # Influence flip: dramatic change
            if zone.influence_us > 70 and zone.influence_ussr > 30:
                gap = zone.influence_us - zone.influence_ussr
                if gap < 20:
                    triggered.append(JumpEvent(
                        type=JumpEventType.CONSEQUENCE,
                        category="DIPLO",
                        title_fr=f"Tensions en {zone.name_fr}",
                        description_fr=f"La competition d'influence en {zone.name_fr} s'intensifie.",
                        target_zone=zone_id,
                        source="world",
                        importance="normal",
                    ))

        # Check world tension consequences
        if state.world_tension > 80:
            triggered.append(JumpEvent(
                type=JumpEventType.WORLD_EVENT,
                category="GLOBAL",
                title_fr="Tensions mondiales critiques",
                description_fr="Les tensions mondiales atteignent un niveau dangereux. Le monde retient son souffle.",
                source="world",
                importance="critical",
            ))

        # DEFCON changes
        if state.world_tension > 85 and state.defcon > 2:
            state.defcon -= 1
            triggered.append(JumpEvent(
                type=JumpEventType.WORLD_EVENT,
                category="DEFCON",
                title_fr=f"DEFCON {state.defcon}",
                description_fr=f"Le niveau DEFCON est abaisse a {state.defcon}. La situation s'aggrave.",
                source="world",
                importance="critical",
                effects={"defcon": -1},
            ))
        elif state.world_tension < 35 and state.defcon < 5:
            state.defcon += 1
            triggered.append(JumpEvent(
                type=JumpEventType.WORLD_EVENT,
                category="DEFCON",
                title_fr=f"DEFCON {state.defcon}",
                description_fr=f"Le niveau DEFCON est releve a {state.defcon}. La situation s'ameliore.",
                source="world",
                importance="normal",
                effects={"defcon": +1},
            ))

        return triggered

    def _advance_time(
        self,
        state: NarrativeWorldState,
        months: int,
        duration: str
    ) -> JumpEvent:
        """Advance game time"""
        for _ in range(max(1, months)):
            state.advance_month()

        duration_labels = {
            "week": "Une semaine s'ecoule",
            "month": "Un mois s'ecoule",
            "quarter": "Un trimestre s'ecoule",
            "year": "Une annee s'ecoule",
            "next_event": "Le temps avance",
        }

        return JumpEvent(
            type=JumpEventType.TIME_PASSAGE,
            category="TIME",
            title_fr=duration_labels.get(duration, "Le temps passe"),
            description_fr=f"{duration_labels.get(duration, 'Le temps passe')}... Nous sommes maintenant en {state.get_date_display('fr')}.",
            source="world",
            importance="minor",
        )

    def _generate_world_events(
        self,
        state: NarrativeWorldState
    ) -> List[JumpEvent]:
        """Generate random world events based on state"""
        events = []

        # Check victory conditions
        end_condition = state.check_victory_conditions()
        if end_condition:
            if state.victory:
                events.append(JumpEvent(
                    type=JumpEventType.RESOLUTION,
                    category="VICTORY",
                    title_fr="Victoire!",
                    description_fr=f"Vous avez gagne! Raison: {end_condition}",
                    source="world",
                    importance="critical",
                ))
            else:
                events.append(JumpEvent(
                    type=JumpEventType.RESOLUTION,
                    category="DEFEAT",
                    title_fr="Defaite...",
                    description_fr=f"Vous avez perdu. Raison: {end_condition}",
                    source="world",
                    importance="critical",
                ))

        return events

    def _order_events(self, events: List[JumpEvent]) -> List[JumpEvent]:
        """Order events for playback"""
        # Sort by importance (critical first) then by type
        importance_order = {"critical": 0, "major": 1, "normal": 2, "minor": 3}
        type_order = {
            JumpEventType.PLAYER_ACTION: 0,
            JumpEventType.ADVERSARY_ACTION: 1,
            JumpEventType.CRISIS: 2,
            JumpEventType.CONSEQUENCE: 3,
            JumpEventType.WORLD_EVENT: 4,
            JumpEventType.TIME_PASSAGE: 5,
            JumpEventType.RESOLUTION: 6,
        }

        def sort_key(e: JumpEvent) -> tuple:
            return (
                type_order.get(e.type, 5),
                importance_order.get(e.importance, 2),
            )

        return sorted(events, key=sort_key)


def create_jump_engine(adversary_ai: AdversaryAI) -> JumpEngine:
    """Factory function to create JumpEngine"""
    return JumpEngine(adversary_ai)
