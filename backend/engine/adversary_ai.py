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
    """AI brain for the USSR adversary"""

    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
        self.memory = AIMemory()

    async def decide_turn(
        self,
        state: NarrativeWorldState,
        use_ollama: bool = True
    ) -> List[AIAction]:
        """Decide what actions to take this turn"""
        adversary = state.adversary

        # Update doctrine based on situation
        self._update_doctrine(adversary, state)

        # Decide number of actions based on pressure
        num_actions = self._decide_action_count(adversary)

        actions = []

        # First: handle critical situations
        critical_action = self._handle_critical_situations(adversary, state)
        if critical_action:
            actions.append(critical_action)
            num_actions -= 1

        # Then: pursue doctrine-based strategy
        for _ in range(num_actions):
            action = self._decide_single_action(adversary, state)
            if action:
                actions.append(action)

        # Optionally enhance with LLM
        if use_ollama and self.ollama and len(actions) > 0:
            try:
                actions = await self._enhance_with_ollama(actions, state)
            except Exception as e:
                logger.warning(f"Ollama enhancement failed: {e}")

        return actions

    def _update_doctrine(self, adversary: AdversaryState, state: NarrativeWorldState):
        """Update doctrine based on current situation"""
        total_pressure = adversary.get_total_pressure()

        # Calculate player's strength
        us_zones = sum(1 for z in state.zones.values() if z.get_dominant_power() == "US")
        player_strength = (
            state.player.political_capital * 0.3 +
            state.player.international_reputation * 0.3 +
            us_zones / len(state.zones) * 100 * 0.4
        )

        # High pressure: need to act
        if total_pressure > 80:
            if adversary.risk_tolerance > 60:
                adversary.doctrine = AdversaryDoctrine.ARMS_RACE
            else:
                adversary.doctrine = AdversaryDoctrine.CONSOLIDATION
            return

        # Crisis situation (DEFCON low)
        if state.defcon <= 2:
            if adversary.risk_tolerance > 70:
                # Maintain pressure
                adversary.doctrine = AdversaryDoctrine.ARMS_RACE
            else:
                # Seek way out
                adversary.doctrine = AdversaryDoctrine.DETENTE
            return

        # Player is weak: expand
        if player_strength < 40:
            adversary.doctrine = AdversaryDoctrine.EXPANSION
            return

        # Player is strong: destabilize or build up
        if player_strength > 70:
            if random.random() > 0.5:
                adversary.doctrine = AdversaryDoctrine.DESTABILIZATION
            else:
                adversary.doctrine = AdversaryDoctrine.ARMS_RACE
            return

        # Check memory for patterns
        recent_provocations = sum(1 for a in self.memory.player_actions[-5:]
                                   if a["type"] in ["threat", "military_demo", "blockade"])
        if recent_provocations >= 2:
            # Player is aggressive
            adversary.doctrine = AdversaryDoctrine.ARMS_RACE
            return

        # Default: maintain current or shift to expansion
        if random.random() > 0.7:
            adversary.doctrine = AdversaryDoctrine.EXPANSION

    def _decide_action_count(self, adversary: AdversaryState) -> int:
        """Decide how many actions to take"""
        base = 2

        # High pressure = more desperate actions
        if adversary.get_total_pressure() > 70:
            base += 1

        # Impulsive leader = more actions
        if adversary.impulsivity > 70:
            base += 1

        # Consolidation = fewer actions
        if adversary.doctrine == AdversaryDoctrine.CONSOLIDATION:
            base -= 1

        return max(1, min(4, base))

    def _handle_critical_situations(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> Optional[AIAction]:
        """Handle critical situations that require immediate response"""

        # DEFCON 2 or lower: consider de-escalation or brinkmanship
        if state.defcon <= 2:
            if adversary.risk_tolerance < 50:
                return AIAction(
                    action_type=AIActionType.PROPOSE_TALKS,
                    target_country="USA",
                    intensity=70,
                    reason="DEFCON critical, seeking negotiated solution",
                    reason_fr="DEFCON critique, recherche de solution negociee",
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

        # Economic pressure critical
        if adversary.pressure_economy > 85:
            return AIAction(
                action_type=AIActionType.ECONOMIC_AID,
                target_zone=self._find_priority_zone(adversary, state),
                intensity=60,
                reason="Economic pressure critical, securing resources",
                reason_fr="Pression economique critique, securisation des ressources",
                effects={"pressure_economy": -10},
            )

        # Army pressure high
        if adversary.pressure_army > 80:
            return AIAction(
                action_type=AIActionType.MILITARY_DEMO,
                target_zone=self._find_contested_zone(state),
                intensity=70,
                reason="Military needs a show of force",
                reason_fr="L'armee a besoin d'une demonstration de force",
                effects={"pressure_army": -15, "world_tension": +10},
            )

        return None

    def _decide_single_action(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> Optional[AIAction]:
        """Decide a single action based on doctrine"""

        doctrine_actions = {
            AdversaryDoctrine.EXPANSION: self._expansion_action,
            AdversaryDoctrine.DESTABILIZATION: self._destab_action,
            AdversaryDoctrine.ARMS_RACE: self._arms_race_action,
            AdversaryDoctrine.DETENTE: self._detente_action,
            AdversaryDoctrine.CONSOLIDATION: self._consolidation_action,
        }

        action_generator = doctrine_actions.get(adversary.doctrine, self._expansion_action)
        return action_generator(adversary, state)

    def _expansion_action(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> AIAction:
        """Generate expansion-focused action"""
        # Find target zone (contested or weak US influence)
        target_zone = None
        best_score = -100

        for zone_id, zone in state.zones.items():
            if zone_id in adversary.priority_zones:
                score = 50
            else:
                score = 0

            # Prefer contested zones
            if zone.get_dominant_power() == "contested":
                score += 30
            # Or zones where USSR is close
            elif zone.influence_ussr > zone.influence_us - 20:
                score += 20

            # Avoid very stable zones
            if zone.stability > 70:
                score -= 20

            if score > best_score:
                best_score = score
                target_zone = zone_id

        action_types = [
            AIActionType.REINFORCE_ZONE,
            AIActionType.PROXY_WAR,
            AIActionType.ECONOMIC_AID,
            AIActionType.PROPAGANDA,
        ]

        # Choose based on situation
        zone = state.zones.get(target_zone)
        if zone and zone.stability < 40:
            action_type = AIActionType.PROXY_WAR
        elif zone and zone.control_ussr < 30:
            action_type = AIActionType.REINFORCE_ZONE
        else:
            action_type = random.choice([AIActionType.PROPAGANDA, AIActionType.ECONOMIC_AID])

        intensity = 50 + adversary.impulsivity // 5

        return AIAction(
            action_type=action_type,
            target_zone=target_zone,
            intensity=intensity,
            reason=f"Expanding influence in {target_zone}",
            reason_fr=f"Extension de l'influence en {target_zone}",
            visible_to_player=action_type != AIActionType.PROXY_WAR,
            effects=self._calculate_effects(action_type, target_zone, intensity),
        )

    def _destab_action(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> AIAction:
        """Generate destabilization-focused action"""
        # Find US-aligned zone to destabilize
        target_zone = None
        best_score = -100

        for zone_id, zone in state.zones.items():
            if zone.get_dominant_power() != "US":
                continue

            score = zone.influence_us - zone.stability
            if zone.has_crisis:
                score += 30
            if zone_id in adversary.priority_zones:
                score += 20

            if score > best_score:
                best_score = score
                target_zone = zone_id

        if not target_zone:
            # No good target, switch to propaganda
            target_zone = self._find_contested_zone(state)

        action_types = [
            AIActionType.DESTABILIZE,
            AIActionType.SUPPORT_REBELS,
            AIActionType.PROPAGANDA,
            AIActionType.INTEL_OP,
        ]

        action_type = random.choice(action_types)
        intensity = 40 + random.randint(0, 30)

        return AIAction(
            action_type=action_type,
            target_zone=target_zone,
            intensity=intensity,
            reason=f"Destabilizing US influence in {target_zone}",
            reason_fr=f"Destabilisation de l'influence US en {target_zone}",
            visible_to_player=random.random() > 0.5,
            effects=self._calculate_effects(action_type, target_zone, intensity),
        )

    def _arms_race_action(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> AIAction:
        """Generate arms race-focused action"""
        action_types = [
            AIActionType.ARMS_BUILDUP,
            AIActionType.NUCLEAR_ADVANCE,
            AIActionType.MILITARY_DEMO,
            AIActionType.BUILD_BASE,
        ]

        # Prioritize based on player actions
        recent_player_military = sum(1 for a in self.memory.player_actions[-5:]
                                      if "military" in a["type"].lower() or "reinforce" in a["type"].lower())

        if recent_player_military >= 2:
            # Match player buildup
            action_type = random.choice([AIActionType.ARMS_BUILDUP, AIActionType.NUCLEAR_ADVANCE])
        else:
            action_type = random.choice(action_types)

        target_zone = None
        if action_type in [AIActionType.MILITARY_DEMO, AIActionType.BUILD_BASE]:
            target_zone = self._find_priority_zone(adversary, state)

        intensity = 60 + adversary.impulsivity // 4

        return AIAction(
            action_type=action_type,
            target_zone=target_zone,
            intensity=intensity,
            reason="Military buildup to maintain parity",
            reason_fr="Renforcement militaire pour maintenir la parite",
            visible_to_player=True,
            effects=self._calculate_effects(action_type, target_zone, intensity),
        )

    def _detente_action(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> AIAction:
        """Generate detente-focused action"""
        # Check what we can concede (P5: forbidden concessions)
        can_negotiate_topics = []

        for topic in ["arms_control", "trade", "cultural_exchange", "space"]:
            if topic not in adversary.forbidden_concessions:
                can_negotiate_topics.append(topic)

        action_types = [
            AIActionType.PROPOSE_TALKS,
            AIActionType.TRADE_DEAL,
            AIActionType.WITHDRAW_ZONE,
        ]

        # Cannot concede? Then consolidate instead
        if not can_negotiate_topics or adversary.get_total_pressure() > 70:
            return AIAction(
                action_type=AIActionType.CONSOLIDATE,
                intensity=50,
                reason="Internal pressure prevents concessions",
                reason_fr="La pression interne empeche les concessions",
                effects={"pressure_party": -5},
            )

        action_type = random.choice(action_types)
        intensity = 40 + random.randint(0, 20)

        if action_type == AIActionType.WITHDRAW_ZONE:
            # Find a zone where we can withdraw (not priority)
            for zone_id, zone in state.zones.items():
                if zone_id not in adversary.priority_zones and zone.influence_ussr > 40:
                    return AIAction(
                        action_type=action_type,
                        target_zone=zone_id,
                        intensity=intensity,
                        reason=f"Withdrawing from {zone_id} as goodwill gesture",
                        reason_fr=f"Retrait de {zone_id} en signe de bonne volonte",
                        effects={"world_tension": -10, "trust_usa": +10},
                    )

        return AIAction(
            action_type=action_type,
            target_country="USA",
            intensity=intensity,
            reason="Seeking diplomatic solution",
            reason_fr="Recherche d'une solution diplomatique",
            effects={"world_tension": -10},
        )

    def _consolidation_action(
        self,
        adversary: AdversaryState,
        state: NarrativeWorldState
    ) -> AIAction:
        """Generate consolidation-focused action"""
        # Focus on internal stability and existing gains
        action_types = [
            AIActionType.CONSOLIDATE,
            AIActionType.ECONOMIC_AID,
            AIActionType.PROPAGANDA,
        ]

        # Find zones where USSR is dominant but could lose
        target_zone = None
        for zone_id, zone in state.zones.items():
            if zone.get_dominant_power() == "USSR" and zone.stability < 50:
                target_zone = zone_id
                break

        if not target_zone:
            # Just internal consolidation
            return AIAction(
                action_type=AIActionType.CONSOLIDATE,
                intensity=50,
                reason="Internal consolidation",
                reason_fr="Consolidation interne",
                effects={"pressure_party": -10, "pressure_economy": -5},
            )

        action_type = random.choice([AIActionType.ECONOMIC_AID, AIActionType.PROPAGANDA])
        intensity = 40 + random.randint(0, 20)

        return AIAction(
            action_type=action_type,
            target_zone=target_zone,
            intensity=intensity,
            reason=f"Consolidating position in {target_zone}",
            reason_fr=f"Consolidation de la position en {target_zone}",
            effects=self._calculate_effects(action_type, target_zone, intensity),
        )

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

        Returns list of planned actions as dicts (for JSON storage in state)
        """
        adversary = state.adversary

        # Update doctrine based on current situation
        self._update_doctrine(adversary, state)

        # Decide action count (usually 1-3 actions)
        num_actions = self._decide_action_count(adversary)

        planned_actions = []

        # Handle critical situations first
        critical = self._handle_critical_situations(adversary, state)
        if critical:
            planned_actions.append(self._action_to_dict(critical))
            num_actions -= 1

        # Plan doctrine-based actions
        for _ in range(num_actions):
            action = self._decide_single_action(adversary, state)
            if action:
                planned_actions.append(self._action_to_dict(action))

        # Store in state (hidden from player)
        state.adversary_action_queue = planned_actions
        state.adversary_planned = True

        logger.info(f"Adversary planned {len(planned_actions)} actions (hidden)")
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
                state.world_tension = max(0, min(100, state.world_tension + delta))
                result["changes"]["world_tension"] = delta

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
