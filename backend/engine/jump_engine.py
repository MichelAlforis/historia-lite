"""Jump Engine for Historia Narrative (PaxHistoria-style)

The Jump Forward mechanic is the core of PaxHistoria gameplay:
1. Player accumulates actions in queue
2. Player clicks "Jump Forward" (>>> button)
3. Engine resolves all actions (player + adversary)
4. Events are generated with causality
5. Player reads events one by one (Save/Intervene)

This engine handles step 3-4: resolution and event generation.

IMPORTANT: Les metriques restent INTERNES au moteur.
Le joueur ne voit QUE des scenes narratives composees par le Chef d'Orchestre.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .narrative_state import NarrativeWorldState, GamePhase
from .action_queue import ActionQueue, QueuedAction
from .adversary_ai import AdversaryAI, AIAction
from .narrative_orchestrator import (
    NarrativeOrchestrator,
    NarrativeScene,
    compose_narrative_scene,
    get_orchestrator,
)

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

    # Scene narrative associee (composee par le Chef d'Orchestre)
    narrative_scene: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON"""
        result = {
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
        # Ajouter la scene narrative si presente
        if self.narrative_scene:
            result["narrative_scene"] = self.narrative_scene
        return result


# =============================================================================
# JUMP ENGINE
# =============================================================================

class JumpEngine:
    """Engine for resolving Jump Forward

    ARCHITECTURE:
    - Metriques: internes au moteur, jamais montrees directement
    - Narratif: le Chef d'Orchestre compose des scenes pour le joueur
    - Le joueur VIT une histoire, pas des chiffres
    """

    def __init__(self, adversary_ai: AdversaryAI):
        self.adversary_ai = adversary_ai
        self.orchestrator = get_orchestrator()

    async def execute_jump(
        self,
        state: NarrativeWorldState,
        duration: str
    ) -> List[JumpEvent]:
        """Execute Jump Forward and generate events

        Main entry point for jump resolution.

        FLOW:
        1. Resoudre les actions (metriques internes)
        2. Pour CHAQUE evenement, composer une scene narrative
        3. Retourner des scenes pretes a afficher
        """
        events: List[JumpEvent] = []

        # Contexte pour le Chef d'Orchestre
        world_context = {
            "year": state.year,
            "month": state.month,
            "defcon": state.defcon,
            "tension": state.world_tension,
            "scenario_seed": state.scenario_seed.value if hasattr(state, 'scenario_seed') else None,
        }
        all_zones = state.zones  # Pour effets domino

        # 1. Get player actions from queue
        queue = state.get_action_queue()
        player_actions = queue.get_active_actions()

        # 2. Get adversary actions (should already be planned)
        adversary_results = await self.adversary_ai.execute_planned_actions(state)

        # 3. Resolve player actions + COMPOSE NARRATIVE SCENES
        for action in player_actions:
            event = await self._resolve_player_action(action, state, world_context, all_zones)
            events.append(event)

        # 4. Add adversary action events + COMPOSE NARRATIVE SCENES
        for result in adversary_results:
            action_data = result["action"]
            if action_data.get("visible_to_player", True):
                event = await self._create_adversary_event(
                    action_data, result["result"], world_context, all_zones, state
                )
                events.append(event)

        # 5. Check for triggered events (consequences, crises)
        triggered = await self._check_triggered_events(state, events, world_context, all_zones)
        events.extend(triggered)

        # 6. Advance time
        months = DURATION_MONTHS.get(JumpDuration(duration), 1)
        time_event = await self._advance_time(state, months, duration, world_context)
        events.append(time_event)

        # 7. Check world events (based on tensions, stability)
        world_events = await self._generate_world_events(state, world_context, all_zones)
        events.extend(world_events)

        # 8. Order events by importance and causality
        events = self._order_events(events)

        logger.info(f"Jump executed: {len(events)} events generated with narrative scenes")
        return events

    async def _resolve_player_action(
        self,
        action: QueuedAction,
        state: NarrativeWorldState,
        context: Dict[str, Any],
        all_zones: Dict
    ) -> JumpEvent:
        """Resolve a single player action and compose narrative scene"""
        # Spend political capital
        state.player.spend_capital(action.political_cost)

        # Apply effects based on action type (INTERNAL METRICS - hidden from player)
        effects_applied = {}

        # 1) EFFETS GLOBAUX - toujours appliques (pas conditionnes a une zone)
        for effect_key, value in action.predicted_effects.items():
            if effect_key == "world_tension":
                state.world_tension = max(0, min(100, state.world_tension + value))
                effects_applied["world_tension"] = value
                logger.debug(f"Applied world_tension {value:+d} -> {state.world_tension}")
            elif effect_key == "defcon":
                state.defcon = max(1, min(5, state.defcon + value))
                effects_applied["defcon"] = value
                logger.debug(f"Applied defcon {value:+d} -> {state.defcon}")
            elif effect_key == "crisis_intensity" and action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.crisis_intensity = max(0, min(100, zone.crisis_intensity + value))
                    effects_applied["crisis_intensity"] = value
                    logger.debug(f"Applied crisis_intensity {value:+d} to {action.target_zone}")

        # 2) EFFETS DE ZONE - seulement si zone valide
        if action.target_zone and action.target_zone in state.zones:
            zone = state.zones[action.target_zone]

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
                elif effect_key == "influence_ussr":
                    zone.influence_ussr = max(0, min(100, zone.influence_ussr + value))
                    effects_applied["influence_ussr"] = value

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

        # COMPOSE NARRATIVE SCENE via le Chef d'Orchestre!
        narrative_scene = await compose_narrative_scene(
            event_type=action.intention_type,
            zone_id=action.target_zone,
            effects=effects_applied,
            context=context,
            importance=importance,
            player_caused=True,
            actor_country="USA",
            target_countries=[action.target_actor] if action.target_actor else [],
            all_zones=all_zones,
        )

        # Log action pour le systeme de Fronts Vivants
        if action.target_zone:
            # Determiner l'intensite depuis le risk_level
            intensity_map = {"low": "light", "medium": "moderate", "high": "heavy", "extreme": "heavy"}
            intensity = intensity_map.get(action.risk_level, "moderate")

            # Determiner la visibilite selon le type d'action
            visibility = "covert" if "COV" in action.intention_type else "public"

            state.log_action(
                zone_id=action.target_zone,
                actor="usa",
                action_type=action.intention_type,
                intensity=intensity,
                payload_fr=action.description_fr,
                visibility=visibility,
            )

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
            narrative_scene=narrative_scene,  # Scene narrative prete!
        )

    async def _create_adversary_event(
        self,
        action_data: Dict[str, Any],
        result: Dict[str, Any],
        context: Dict[str, Any],
        all_zones: Dict,
        state: NarrativeWorldState
    ) -> JumpEvent:
        """Create event from adversary action with narrative scene"""
        action_type = action_data.get("action_type", "unknown")
        category = action_type.split("_")[0] if "_" in action_type else "USSR"

        importance = "normal"
        if "military" in action_type.lower() or "nuclear" in action_type.lower():
            importance = "major"
        if "threaten" in action_type.lower():
            importance = "major"

        # COMPOSE NARRATIVE SCENE via le Chef d'Orchestre!
        narrative_scene = await compose_narrative_scene(
            event_type=action_type,
            zone_id=action_data.get("target_zone"),
            effects=result.get("changes", {}),
            context=context,
            importance=importance,
            player_caused=False,  # L'adversaire a agi
            actor_country="USSR",
            target_countries=[action_data.get("target_country")] if action_data.get("target_country") else [],
            all_zones=all_zones,
        )

        # Log action pour le systeme de Fronts Vivants
        target_zone = action_data.get("target_zone")
        if target_zone:
            # Determiner l'intensite depuis l'importance
            intensity = "heavy" if importance in ["major", "critical"] else "moderate"

            # Determiner la visibilite selon le type d'action
            visibility = "covert" if "covert" in action_type.lower() or "intel" in action_type.lower() else "public"

            state.log_action(
                zone_id=target_zone,
                actor="ussr",
                action_type=action_type,
                intensity=intensity,
                payload_fr=action_data.get("reason_fr", "Action sovietique"),
                visibility=visibility,
            )

        return JumpEvent(
            type=JumpEventType.ADVERSARY_ACTION,
            category=category,
            title_fr=action_data.get("reason_fr", "Action sovietique"),
            description_fr=f"L'URSS a agi: {action_data.get('reason_fr', 'Action inconnue')}",
            target_zone=target_zone,
            target_actor=action_data.get("target_country"),
            source="adversary",
            effects=result.get("changes", {}),
            importance=importance,
            narrative_scene=narrative_scene,  # Scene narrative prete!
        )

    async def _check_triggered_events(
        self,
        state: NarrativeWorldState,
        existing_events: List[JumpEvent],
        context: Dict[str, Any],
        all_zones: Dict
    ) -> List[JumpEvent]:
        """Check for events triggered by actions with narrative scenes"""
        triggered = []

        # Check each zone for consequences
        for zone_id, zone in state.zones.items():
            # Crisis trigger: stability very low
            if zone.stability < 25 and not zone.has_crisis:
                zone.has_crisis = True
                zone.crisis_type = "instability"

                # Scene narrative pour la crise
                narrative_scene = await compose_narrative_scene(
                    event_type="crisis_erupted",
                    zone_id=zone_id,
                    effects={"stability": -10},
                    context=context,
                    importance="major",
                    player_caused=False,
                    all_zones=all_zones,
                )

                triggered.append(JumpEvent(
                    type=JumpEventType.CRISIS,
                    category="CRISIS",
                    title_fr=f"Crise en {zone.name_fr}",
                    description_fr=f"L'instabilite en {zone.name_fr} atteint un point critique. Une crise eclate.",
                    target_zone=zone_id,
                    source="world",
                    importance="major",
                    effects={"stability": -10},
                    narrative_scene=narrative_scene,
                ))

            # Influence flip: dramatic change
            if zone.influence_us > 70 and zone.influence_ussr > 30:
                gap = zone.influence_us - zone.influence_ussr
                if gap < 20:
                    narrative_scene = await compose_narrative_scene(
                        event_type="influence_conflict",
                        zone_id=zone_id,
                        context=context,
                        importance="normal",
                        all_zones=all_zones,
                    )

                    triggered.append(JumpEvent(
                        type=JumpEventType.CONSEQUENCE,
                        category="DIPLO",
                        title_fr=f"Tensions en {zone.name_fr}",
                        description_fr=f"La competition d'influence en {zone.name_fr} s'intensifie.",
                        target_zone=zone_id,
                        source="world",
                        importance="normal",
                        narrative_scene=narrative_scene,
                    ))

        # Check world tension consequences
        if state.world_tension > 80:
            narrative_scene = await compose_narrative_scene(
                event_type="world_tension_critical",
                context=context,
                importance="critical",
                effects={"tension": state.world_tension},
                all_zones=all_zones,
            )

            triggered.append(JumpEvent(
                type=JumpEventType.WORLD_EVENT,
                category="GLOBAL",
                title_fr="Tensions mondiales critiques",
                description_fr="Les tensions mondiales atteignent un niveau dangereux. Le monde retient son souffle.",
                source="world",
                importance="critical",
                narrative_scene=narrative_scene,
            ))

        # DEFCON changes - can go down to 1 (apocalypse threshold)
        if state.world_tension > 85 and state.defcon > 1:
            state.defcon -= 1
            narrative_scene = await compose_narrative_scene(
                event_type="defcon_lowered",
                context={**context, "defcon": state.defcon},
                importance="critical",
                effects={"defcon": -1},
                all_zones=all_zones,
            )

            triggered.append(JumpEvent(
                type=JumpEventType.WORLD_EVENT,
                category="DEFCON",
                title_fr=f"DEFCON {state.defcon}",
                description_fr=f"Le niveau DEFCON est abaisse a {state.defcon}. La situation s'aggrave.",
                source="world",
                importance="critical",
                effects={"defcon": -1},
                narrative_scene=narrative_scene,
            ))
        elif state.world_tension < 35 and state.defcon < 5:
            state.defcon += 1
            narrative_scene = await compose_narrative_scene(
                event_type="defcon_raised",
                context={**context, "defcon": state.defcon},
                importance="normal",
                effects={"defcon": +1},
                all_zones=all_zones,
            )

            triggered.append(JumpEvent(
                type=JumpEventType.WORLD_EVENT,
                category="DEFCON",
                title_fr=f"DEFCON {state.defcon}",
                description_fr=f"Le niveau DEFCON est releve a {state.defcon}. La situation s'ameliore.",
                source="world",
                importance="normal",
                effects={"defcon": +1},
                narrative_scene=narrative_scene,
            ))

        return triggered

    async def _advance_time(
        self,
        state: NarrativeWorldState,
        months: int,
        duration: str,
        context: Dict[str, Any]
    ) -> JumpEvent:
        """Advance game time - passage du temps narratif"""
        for _ in range(max(1, months)):
            state.advance_month()

        duration_labels = {
            "week": "Une semaine s'ecoule",
            "month": "Un mois s'ecoule",
            "quarter": "Un trimestre s'ecoule",
            "year": "Une annee s'ecoule",
            "next_event": "Le temps avance",
        }

        # Pas de scene narrative complexe pour le passage du temps
        # Juste une transition simple
        return JumpEvent(
            type=JumpEventType.TIME_PASSAGE,
            category="TIME",
            title_fr=duration_labels.get(duration, "Le temps passe"),
            description_fr=f"{duration_labels.get(duration, 'Le temps passe')}... Nous sommes maintenant en {state.get_date_display('fr')}.",
            source="world",
            importance="minor",
        )

    async def _generate_world_events(
        self,
        state: NarrativeWorldState,
        context: Dict[str, Any],
        all_zones: Dict
    ) -> List[JumpEvent]:
        """Generate world events with narrative scenes"""
        events = []

        # Check victory conditions
        end_condition = state.check_victory_conditions()
        if end_condition:
            if state.victory:
                # Scene narrative de victoire epique!
                narrative_scene = await compose_narrative_scene(
                    event_type="victory",
                    context=context,
                    importance="critical",
                    all_zones=all_zones,
                )

                events.append(JumpEvent(
                    type=JumpEventType.RESOLUTION,
                    category="VICTORY",
                    title_fr="Victoire!",
                    description_fr=f"Vous avez gagne! Raison: {end_condition}",
                    source="world",
                    importance="critical",
                    narrative_scene=narrative_scene,
                ))
            else:
                # Scene narrative de defaite sombre
                narrative_scene = await compose_narrative_scene(
                    event_type="defeat",
                    context=context,
                    importance="critical",
                    all_zones=all_zones,
                )

                events.append(JumpEvent(
                    type=JumpEventType.RESOLUTION,
                    category="DEFEAT",
                    title_fr="Defaite...",
                    description_fr=f"Vous avez perdu. Raison: {end_condition}",
                    source="world",
                    importance="critical",
                    narrative_scene=narrative_scene,
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
