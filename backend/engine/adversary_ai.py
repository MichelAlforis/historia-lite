"""Adversary AI for Historia Narrative (PaxHistoria-style)

The USSR AI that plays to WIN, not just reacts.
Based on Plan: P5 - Adversary with Doctrine + Constraints

Key features:
- Doctrine: preferred strategy (expansion, destab, arms race, detente)
- Internal pressures: army, party, economy, opinion
- Forbidden actions: cannot concede if pressure > threshold
- Long-term memory: tracks player actions over turns
- Personality: impulsivity, risk tolerance

PaxHistoria additions:
- plan_turn(): Plans actions during player accumulation (hidden)
- Actions are revealed only at Jump Forward
- Adversary "plays" simultaneously with player

FOG OF WAR (v2):
- L'IA ne lit JAMAIS directement NarrativeWorldState
- Elle utilise AIPerceptionEngine pour obtenir des croyances (beliefs)
- Raisonnement en tags qualitatifs, pas en chiffres
- Factions (KGB/Armee/Politburo) proposent, le leader arbitre
"""
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field

from .narrative_state import (
    NarrativeWorldState,
    AdversaryState,
    AdversaryDoctrine,
    NarrativeZone,
    DiplomacyProfile,
)
from .ai_perception import (
    AIPerceptionEngine,
    WorldObservations,
    AIBeliefs,
    FactionProposal,
    ConfidenceBand,
    ResolveLevel,
    NuclearRisk,
    OpportunityLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# AI ACTION TYPES
# =============================================================================

class AIActionType(str, Enum):
    """Types of actions the AI can take"""
    # Diplomatic
    PROPOSE_TALKS = "propose_talks"
    REJECT_TALKS = "reject_talks"
    THREATEN = "threaten"
    CONCEDE = "concede"
    DEMAND = "demand"

    # Military
    REINFORCE_ZONE = "reinforce_zone"
    WITHDRAW_ZONE = "withdraw_zone"
    MILITARY_DEMO = "military_demo"
    PROXY_WAR = "proxy_war"
    BUILD_BASE = "build_base"

    # Covert
    DESTABILIZE = "destabilize"
    SUPPORT_REBELS = "support_rebels"
    PROPAGANDA = "propaganda"
    INTEL_OP = "intel_op"

    # Economic
    ECONOMIC_AID = "economic_aid"
    TRADE_DEAL = "trade_deal"
    EMBARGO = "embargo"

    # Internal
    CONSOLIDATE = "consolidate"
    ARMS_BUILDUP = "arms_buildup"
    NUCLEAR_ADVANCE = "nuclear_advance"


class AIAction(BaseModel):
    """An action decided by the AI"""
    action_type: AIActionType
    target_zone: Optional[str] = None
    target_country: Optional[str] = None
    intensity: int = Field(default=50, ge=0, le=100)
    reason: str = ""
    reason_fr: str = ""
    visible_to_player: bool = True
    effects: Dict[str, Any] = Field(default_factory=dict)


class AIMemory(BaseModel):
    """AI's memory of player actions and events"""
    player_actions: List[Dict[str, Any]] = Field(default_factory=list)
    broken_promises: int = 0
    military_provocations: int = 0
    successful_negotiations: int = 0
    covert_ops_detected: int = 0
    zones_lost: List[str] = Field(default_factory=list)
    zones_gained: List[str] = Field(default_factory=list)

    def record_player_action(self, action_type: str, target: str, turn: int):
        """Record a player action for future reference"""
        self.player_actions.append({
            "type": action_type,
            "target": target,
            "turn": turn,
        })
        # Keep only last 20 actions
        if len(self.player_actions) > 20:
            self.player_actions = self.player_actions[-20:]


# =============================================================================
# ADVERSARY AI
# =============================================================================

class AdversaryAI:
    """AI brain for the USSR adversary

    FOG OF WAR: L'IA ne lit JAMAIS directement l'etat reel.
    Elle utilise perception_engine pour obtenir des croyances.
    """

    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
        self.memory = AIMemory()
        self.perception_engine = AIPerceptionEngine()
        self.current_beliefs: Optional[AIBeliefs] = None
        self.last_player_actions: List[Dict[str, Any]] = []

    async def decide_turn(
        self,
        state: NarrativeWorldState,
        use_ollama: bool = True
    ) -> List[AIAction]:
        """Decide what actions to take this turn

        FOG OF WAR: Utilise le systeme de perception au lieu de lire l'etat reel.
        """
        adversary = state.adversary

        # === FOG OF WAR: Build observations and beliefs ===
        observations = self.perception_engine.build_observations(
            real_state=state,
            last_player_actions=self.last_player_actions,
        )

        beliefs = self.perception_engine.update_beliefs(
            observations=observations,
            adversary=adversary,
            previous_beliefs=self.current_beliefs,
        )
        self.current_beliefs = beliefs

        # Debug: log belief vs reality (dev only)
        self.perception_engine.log_belief_vs_reality(beliefs, state)

        # === FACTION PROPOSALS: Each faction proposes ===
        proposals = self.perception_engine.get_faction_proposals(beliefs, adversary)

        # === LEADER ARBITRAGE: Choose based on personality ===
        chosen_proposal = self.perception_engine.leader_arbitrates(proposals, adversary)

        # Convert proposal to AIAction
        actions = [self._proposal_to_action(chosen_proposal, adversary)]

        # === LEGACY: Handle critical situations (DEFCON-based) ===
        # Note: This still uses beliefs, not real state
        if beliefs.nuclear_risk == NuclearRisk.CRITICAL:
            critical_action = self._handle_critical_from_beliefs(beliefs, adversary)
            if critical_action:
                actions.insert(0, critical_action)

        # === Add more actions if high pressure ===
        if adversary.get_total_pressure() > 70:
            # Add a second action based on doctrine
            additional = self._decide_action_from_beliefs(beliefs, adversary)
            if additional:
                actions.append(additional)

        # Optionally enhance with LLM
        if use_ollama and self.ollama and len(actions) > 0:
            try:
                actions = await self._enhance_with_ollama(actions, state)
            except Exception as e:
                logger.warning(f"Ollama enhancement failed: {e}")

        return actions

    def _proposal_to_action(
        self,
        proposal: FactionProposal,
        adversary: AdversaryState,
    ) -> AIAction:
        """Convert a faction proposal to an AIAction"""
        # Map proposal action types to AIActionType
        action_map = {
            "destabilize": AIActionType.DESTABILIZE,
            "intel_op": AIActionType.INTEL_OP,
            "military_demo": AIActionType.MILITARY_DEMO,
            "arms_buildup": AIActionType.ARMS_BUILDUP,
            "propose_talks": AIActionType.PROPOSE_TALKS,
            "consolidate": AIActionType.CONSOLIDATE,
            "reinforce_zone": AIActionType.REINFORCE_ZONE,
            "propaganda": AIActionType.PROPAGANDA,
        }

        action_type = action_map.get(proposal.action_type, AIActionType.CONSOLIDATE)

        # Map intensity to numeric value
        intensity_map = {"light": 40, "moderate": 60, "heavy": 80}
        intensity = intensity_map.get(proposal.intensity, 50)

        return AIAction(
            action_type=action_type,
            target_zone=proposal.target_zone,
            target_country=proposal.target_country,
            intensity=intensity,
            reason=f"[{proposal.faction.upper()}] {proposal.rationale}",
            reason_fr=f"[{proposal.faction.upper()}] {proposal.rationale_fr}",
            visible_to_player=proposal.faction != "kgb",  # KGB actions are covert
            effects=self._calculate_effects(action_type, proposal.target_zone, intensity),
        )

    def _handle_critical_from_beliefs(
        self,
        beliefs: AIBeliefs,
        adversary: AdversaryState,
    ) -> Optional[AIAction]:
        """Handle critical situations based on beliefs (not real state)"""
        if beliefs.nuclear_risk == NuclearRisk.CRITICAL:
            if adversary.risk_tolerance < 50:
                return AIAction(
                    action_type=AIActionType.PROPOSE_TALKS,
                    target_country="USA",
                    intensity=70,
                    reason="Nuclear risk critical, seeking negotiated solution",
                    reason_fr="Risque nucleaire critique, recherche de solution negociee",
                    effects={"defcon": +1, "world_tension": -15},
                )
            else:
                return AIAction(
                    action_type=AIActionType.THREATEN,
                    target_country="USA",
                    intensity=80,
                    reason="Refuse to back down under pressure",
                    reason_fr="Refuse de reculer sous la pression",
                    effects={"fear_usa": +20, "world_tension": +10},
                )
        return None

    def _decide_action_from_beliefs(
        self,
        beliefs: AIBeliefs,
        adversary: AdversaryState,
    ) -> Optional[AIAction]:
        """Decide an additional action based on beliefs"""
        # Find a zone with opportunity
        for zone_id, zone_belief in beliefs.zones.items():
            if zone_belief.opportunity_level == OpportunityLevel.RIPE:
                return AIAction(
                    action_type=AIActionType.REINFORCE_ZONE,
                    target_zone=zone_id,
                    intensity=60,
                    reason=f"Opportunity detected in {zone_id}",
                    reason_fr=f"Opportunite detectee en {zone_id}",
                    effects=self._calculate_effects(AIActionType.REINFORCE_ZONE, zone_id, 60),
                )

        # Fallback: consolidate
        return None

    def record_player_action(self, action: Dict[str, Any]):
        """Record a player action for perception system"""
        self.last_player_actions.append(action)
        # Keep only last 10 actions
        if len(self.last_player_actions) > 10:
            self.last_player_actions = self.last_player_actions[-10:]

    def get_ai_errors(self) -> List[Dict[str, Any]]:
        """Get AI perception errors for debrief"""
        errors = self.perception_engine.get_errors()
        return [
            {
                "turn": e.turn,
                "error_type": e.error_type,
                "subject": e.subject,
                "belief": e.belief,
                "reality": e.reality,
                "consequence": e.consequence,
                "consequence_fr": e.consequence_fr,
            }
            for e in errors
        ]

    def get_current_beliefs(self) -> Optional[Dict[str, Any]]:
        """Get current beliefs for debugging/narrative"""
        if not self.current_beliefs:
            return None
        return {
            "player_resolve": self.current_beliefs.player.resolve.value,
            "player_strategy": self.current_beliefs.player.likely_strategy,
            "player_tags": self.current_beliefs.player.tags,
            "nuclear_risk": self.current_beliefs.nuclear_risk.value,
            "global_tension": self.current_beliefs.global_tension.value,
            "opportunity_window": self.current_beliefs.opportunity_window,
            "zones": {
                zone_id: {
                    "stability": zb.stability_band.value,
                    "opportunity": zb.opportunity_level.value,
                    "threat": zb.threat_level.value,
                    "tags": zb.tags,
                }
                for zone_id, zb in self.current_beliefs.zones.items()
            },
        }

    # =========================================================================
    # LEGACY CODE REMOVED (lignes 328-711)
    # Les methodes suivantes ont ete supprimees car remplacees par FOG OF WAR:
    # - _update_doctrine
    # - _decide_action_count
    # - _handle_critical_situations
    # - _decide_single_action
    # - _expansion_action
    # - _destab_action
    # - _arms_race_action
    # - _detente_action
    # - _consolidation_action
    # Le nouveau systeme utilise: perception_engine + faction proposals + beliefs
    # =========================================================================

    def _find_priority_zone(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> str:
        """Find a priority zone for action"""
        for zone_id in adversary.priority_zones:
            if zone_id in state.zones:
                return zone_id
        # Default to contested zone
        return self._find_contested_zone(state)

    def _find_contested_zone(self, state: NarrativeWorldState) -> str:
        """Find a contested zone"""
        for zone_id, zone in state.zones.items():
            if zone.get_dominant_power() == "contested":
                return zone_id
        # Default to central_america (Cuba crisis)
        return "central_america"

    def _calculate_effects(
        self,
        action_type: AIActionType,
        target_zone: Optional[str],
        intensity: int
    ) -> Dict[str, Any]:
        """Calculate expected effects of an action"""
        effects = {}
        base = intensity / 100

        if action_type == AIActionType.REINFORCE_ZONE:
            effects["control_ussr"] = int(15 * base)
            effects["influence_ussr"] = int(10 * base)
            effects["world_tension"] = int(10 * base)

        elif action_type == AIActionType.WITHDRAW_ZONE:
            effects["control_ussr"] = int(-15 * base)
            effects["world_tension"] = int(-10 * base)

        elif action_type == AIActionType.MILITARY_DEMO:
            effects["fear_usa"] = int(15 * base)
            effects["world_tension"] = int(15 * base)

        elif action_type == AIActionType.PROXY_WAR:
            effects["influence_ussr"] = int(15 * base)
            effects["stability"] = int(-20 * base)

        elif action_type == AIActionType.DESTABILIZE:
            effects["influence_us"] = int(-15 * base)
            effects["stability"] = int(-15 * base)

        elif action_type == AIActionType.PROPAGANDA:
            effects["influence_ussr"] = int(5 * base)
            effects["influence_us"] = int(-5 * base)

        elif action_type == AIActionType.ECONOMIC_AID:
            effects["influence_ussr"] = int(10 * base)
            effects["stability"] = int(5 * base)

        elif action_type == AIActionType.ARMS_BUILDUP:
            effects["pressure_army"] = int(-15 * base)
            effects["pressure_economy"] = int(5 * base)

        elif action_type == AIActionType.NUCLEAR_ADVANCE:
            effects["fear_usa"] = int(10 * base)
            effects["world_tension"] = int(10 * base)

        elif action_type == AIActionType.PROPOSE_TALKS:
            effects["world_tension"] = int(-10 * base)
            effects["trust_usa"] = int(5 * base)

        elif action_type == AIActionType.THREATEN:
            effects["fear_usa"] = int(20 * base)
            effects["trust_usa"] = int(-10 * base)
            effects["world_tension"] = int(10 * base)

        elif action_type == AIActionType.CONSOLIDATE:
            effects["pressure_party"] = int(-10 * base)
            effects["pressure_economy"] = int(-5 * base)

        return effects

    async def _enhance_with_ollama(
        self,
        actions: List[AIAction],
        state: NarrativeWorldState
    ) -> List[AIAction]:
        """Optionally enhance actions with LLM reasoning"""
        # Build context
        context = {
            "year": state.year,
            "month": state.month,
            "defcon": state.defcon,
            "world_tension": state.world_tension,
            "doctrine": state.adversary.doctrine.value,
            "pressure": state.adversary.get_total_pressure(),
            "player_capital": state.player.political_capital,
            "scenario_seed": state.scenario_seed.value if hasattr(state, 'scenario_seed') else None,
            "actions": [{"type": a.action_type.value, "target": a.target_zone or a.target_country}
                       for a in actions],
        }

        system_prompt = """Tu es le conseiller strategique de l'URSS pendant la Guerre Froide.
Analyse les actions proposees et suggere des ajustements tactiques.
Garde en tete:
- La doctrine actuelle du Kremlin
- Les pressions internes (armee, parti, economie)
- La necessite de paraitre fort sans provoquer une guerre nucleaire

Reponds en JSON avec format:
{
  "analysis": "courte analyse",
  "adjustments": [{"action_index": 0, "new_intensity": 60, "reason": "..."}]
}
"""

        try:
            response = await self.ollama.generate(
                model="llama3:8b",
                prompt=f"Contexte: {context}\n\nAnalyse les actions:",
                system=system_prompt,
                format="json"
            )

            import json
            data = json.loads(response)

            # Apply adjustments
            for adj in data.get("adjustments", []):
                idx = adj.get("action_index", 0)
                if 0 <= idx < len(actions):
                    if "new_intensity" in adj:
                        actions[idx].intensity = adj["new_intensity"]
                    if "reason" in adj:
                        actions[idx].reason_fr += f" ({adj['reason']})"

        except Exception as e:
            logger.warning(f"Ollama enhancement failed: {e}")

        return actions

    def react_to_player_action(
        self,
        player_action_type: str,
        target: str,
        state: NarrativeWorldState
    ) -> Optional[AIAction]:
        """React to a specific player action"""
        adversary = state.adversary

        # Record in memory
        self.memory.record_player_action(player_action_type, target, state.turn)

        # Check for immediate reaction
        if "threat" in player_action_type.lower():
            self.memory.military_provocations += 1

            # Impulsive leader reacts immediately
            if adversary.impulsivity > 60:
                return AIAction(
                    action_type=AIActionType.THREATEN,
                    target_country="USA",
                    intensity=70,
                    reason="Counter-threat to US provocation",
                    reason_fr="Contre-menace face a la provocation US",
                    effects={"fear_usa": +10, "world_tension": +5},
                )

        if "blockade" in player_action_type.lower():
            # Serious escalation
            if adversary.risk_tolerance > 50:
                return AIAction(
                    action_type=AIActionType.MILITARY_DEMO,
                    target_zone=target,
                    intensity=80,
                    reason="Testing US resolve on blockade",
                    reason_fr="Test de la determination US sur le blocus",
                    effects={"world_tension": +20, "defcon": -1},
                )
            else:
                return AIAction(
                    action_type=AIActionType.PROPOSE_TALKS,
                    target_country="USA",
                    intensity=60,
                    reason="Seeking diplomatic solution to blockade",
                    reason_fr="Recherche d'une solution diplomatique au blocus",
                    effects={"world_tension": -5},
                )

        if "negotiate" in player_action_type.lower():
            self.memory.successful_negotiations += 1
            # Usually accept talks (unless forbidden)
            if adversary.get_total_pressure() < 70:
                return AIAction(
                    action_type=AIActionType.PROPOSE_TALKS,
                    target_country="USA",
                    intensity=50,
                    reason="Accepting diplomatic overture",
                    reason_fr="Acceptation de l'ouverture diplomatique",
                    effects={"trust_usa": +5},
                )

        if "covert" in player_action_type.lower() or "destab" in player_action_type.lower():
            self.memory.covert_ops_detected += 1
            # Retaliate in kind
            return AIAction(
                action_type=AIActionType.DESTABILIZE,
                target_zone="europe_west" if target in ["europe_east", "central_america"] else target,
                intensity=60,
                reason="Retaliating for covert operations",
                reason_fr="Represailles pour operations clandestines",
                visible_to_player=False,
                effects={"influence_us": -10},
            )

        return None

    # =========================================================================
    # PAXHISTORIA: PARALLEL PLANNING
    # =========================================================================

    async def plan_turn(
        self,
        state: NarrativeWorldState,
        use_ollama: bool = False
    ) -> List[Dict[str, Any]]:
        """Plan adversary actions during player accumulation (PaxHistoria-style)

        Called when player queues their first action.
        Actions are stored hidden and revealed at Jump Forward.

        FOG OF WAR: Uses perception engine instead of reading real state.

        Returns list of planned actions as dicts (for JSON storage in state)
        """
        adversary = state.adversary

        # === FOG OF WAR: Build observations and beliefs ===
        observations = self.perception_engine.build_observations(
            real_state=state,
            last_player_actions=self.last_player_actions,
        )

        beliefs = self.perception_engine.update_beliefs(
            observations=observations,
            adversary=adversary,
            previous_beliefs=self.current_beliefs,
        )
        self.current_beliefs = beliefs

        # === FACTION PROPOSALS ===
        proposals = self.perception_engine.get_faction_proposals(beliefs, adversary)

        # === LEADER ARBITRAGE ===
        chosen_proposal = self.perception_engine.leader_arbitrates(proposals, adversary)

        # Convert to action
        main_action = self._proposal_to_action(chosen_proposal, adversary)
        planned_actions = [self._action_to_dict(main_action)]

        # === Additional action if opportunity window ===
        if beliefs.opportunity_window:
            additional = self._decide_action_from_beliefs(beliefs, adversary)
            if additional:
                planned_actions.append(self._action_to_dict(additional))

        # === Critical situation handling ===
        if beliefs.nuclear_risk == NuclearRisk.CRITICAL:
            critical = self._handle_critical_from_beliefs(beliefs, adversary)
            if critical:
                planned_actions.insert(0, self._action_to_dict(critical))

        # Store in state (hidden from player)
        state.adversary_action_queue = planned_actions
        state.adversary_planned = True

        logger.info(f"Adversary planned {len(planned_actions)} actions via FOG OF WAR (hidden)")
        return planned_actions

    def _action_to_dict(self, action: AIAction) -> Dict[str, Any]:
        """Convert AIAction to dict for JSON storage"""
        return {
            "action_type": action.action_type.value,
            "target_zone": action.target_zone,
            "target_country": action.target_country,
            "intensity": action.intensity,
            "reason": action.reason,
            "reason_fr": action.reason_fr,
            "visible_to_player": action.visible_to_player,
            "effects": action.effects,
        }

    def actions_from_queue(
        self,
        queue: List[Dict[str, Any]]
    ) -> List[AIAction]:
        """Convert stored queue back to AIAction objects"""
        actions = []
        for item in queue:
            action = AIAction(
                action_type=AIActionType(item["action_type"]),
                target_zone=item.get("target_zone"),
                target_country=item.get("target_country"),
                intensity=item.get("intensity", 50),
                reason=item.get("reason", ""),
                reason_fr=item.get("reason_fr", ""),
                visible_to_player=item.get("visible_to_player", True),
                effects=item.get("effects", {}),
            )
            actions.append(action)
        return actions

    async def execute_planned_actions(
        self,
        state: NarrativeWorldState
    ) -> List[Dict[str, Any]]:
        """Execute planned actions during Jump Forward

        Called when player triggers Jump Forward.
        Returns list of executed action results.
        """
        results = []

        # Get planned actions
        planned = state.adversary_action_queue
        if not planned:
            # No planned actions, generate some now
            actions = await self.decide_turn(state, use_ollama=False)
            planned = [self._action_to_dict(a) for a in actions]

        # Convert to AIAction objects
        actions = self.actions_from_queue(planned)

        # Apply effects
        for action in actions:
            result = self._apply_action_effects(action, state)
            results.append({
                "action": self._action_to_dict(action),
                "result": result,
            })

        # Clear the queue
        state.adversary_action_queue = []
        state.adversary_planned = False

        logger.info(f"Adversary executed {len(results)} planned actions")
        return results

    def _apply_action_effects(
        self,
        action: AIAction,
        state: NarrativeWorldState
    ) -> Dict[str, Any]:
        """Apply the effects of an adversary action"""
        result = {
            "success": True,
            "changes": {},
        }

        for effect_name, delta in action.effects.items():
            if "influence_ussr" in effect_name and action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.influence_ussr = max(0, min(100, zone.influence_ussr + delta))
                    result["changes"][f"zone_{action.target_zone}_influence_ussr"] = delta

            elif "influence_us" in effect_name and action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.influence_us = max(0, min(100, zone.influence_us + delta))
                    result["changes"][f"zone_{action.target_zone}_influence_us"] = delta

            elif "control_ussr" in effect_name and action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.control_ussr = max(0, min(100, zone.control_ussr + delta))
                    result["changes"][f"zone_{action.target_zone}_control_ussr"] = delta

            elif "stability" in effect_name and action.target_zone:
                zone = state.zones.get(action.target_zone)
                if zone:
                    zone.stability = max(0, min(100, zone.stability + delta))
                    result["changes"][f"zone_{action.target_zone}_stability"] = delta

            elif "world_tension" in effect_name:
                # Diminishing returns: plus la tension est haute, moins chaque point pousse
                # A 70 tension, l'effet est reduit de moitie
                damping = max(0.25, 1.0 - (state.world_tension / 140.0))
                effective_delta = int(round(delta * damping))
                state.world_tension = max(0, min(100, state.world_tension + effective_delta))
                result["changes"]["world_tension"] = effective_delta

            elif "defcon" in effect_name:
                state.defcon = max(1, min(5, state.defcon + delta))
                result["changes"]["defcon"] = delta

            elif "fear_usa" in effect_name:
                diplo = state.player.get_diplomacy_with("USSR")
                diplo.fear = max(0, min(100, diplo.fear + delta))
                result["changes"]["fear"] = delta

            elif "trust_usa" in effect_name:
                diplo = state.player.get_diplomacy_with("USSR")
                diplo.trust = max(0, min(100, diplo.trust + delta))
                result["changes"]["trust"] = delta

            elif "pressure_" in effect_name:
                attr = effect_name
                if hasattr(state.adversary, attr):
                    current = getattr(state.adversary, attr)
                    setattr(state.adversary, attr, max(0, min(100, current + delta)))
                    result["changes"][attr] = delta

        return result

    def update_pressures(self, state: NarrativeWorldState, events: List[Dict]):
        """Update internal pressures based on events"""
        adversary = state.adversary

        # Count USSR zones
        ussr_zones = sum(1 for z in state.zones.values() if z.get_dominant_power() == "USSR")
        total_zones = len(state.zones)

        # Army pressure
        if ussr_zones < total_zones * 0.3:
            adversary.pressure_army += 5
        elif ussr_zones > total_zones * 0.5:
            adversary.pressure_army -= 5

        # Party pressure based on reputation
        if self.memory.broken_promises > 2:
            adversary.pressure_party += 10
        if self.memory.successful_negotiations > 3:
            adversary.pressure_party -= 5

        # Economic pressure (gradual increase over time)
        adversary.pressure_economy += random.randint(0, 3)

        # Events can affect pressures
        for event in events:
            if event.get("type") == "victory":
                adversary.pressure_army -= 10
                adversary.pressure_party -= 5
            elif event.get("type") == "defeat":
                adversary.pressure_army += 15
                adversary.pressure_party += 10

        # Clamp values
        adversary.pressure_army = max(0, min(100, adversary.pressure_army))
        adversary.pressure_party = max(0, min(100, adversary.pressure_party))
        adversary.pressure_economy = max(0, min(100, adversary.pressure_economy))
