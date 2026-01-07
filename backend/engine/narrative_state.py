"""Narrative Mode World State for Historia Narrative (PaxHistoria Style)

Extends the base World state with:
- Player variables (political_capital, domestic_stability, international_reputation, intel_exposure)
- Adversary variables (doctrine, pressures, risk_tolerance)
- Zone variables (influence_us, influence_ussr, control_us, control_ussr, stability)
- Diplomacy variables (trust, fear, respect, leverage per actor)
- Global variables (world_tension, defcon)

PaxHistoria-style additions:
- GamePhase: ACCUMULATING, JUMPING, PLAYBACK (replaces turn-based)
- Action Queue: Player actions accumulated before Jump Forward
- Adversary Queue: Hidden USSR actions planned during accumulation

Based on Plan: Historia Narrative - WorldState Contract v0 + PaxHistoria model
"""
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from engine.action_queue import ActionQueue, QueuedAction
    from engine.silence_mechanics import SilenceState

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class AdversaryDoctrine(str, Enum):
    """Strategic doctrine of the adversary (USSR)"""
    EXPANSION = "expansion"        # Aggressive expansion, proxy wars
    DESTABILIZATION = "destab"     # Destabilize western allies
    ARMS_RACE = "arms_race"        # Military buildup focus
    DETENTE = "detente"            # Seek negotiations, reduce tensions
    CONSOLIDATION = "consolidation"  # Internal focus, protect existing gains


class TurnPhase(str, Enum):
    """Current phase of a turn (legacy - kept for compatibility)"""
    PLAYER_INPUT = "player_input"          # Waiting for player text
    INTENT_REVIEW = "intent_review"        # Player reviews parsed intentions
    ACTION_CONFIRM = "action_confirm"      # Player confirms actions
    DIPLOMACY = "diplomacy"                # Diplomatic exchanges if any
    ADVERSARY_TURN = "adversary_turn"      # AI plays its turn
    RESOLUTION = "resolution"              # Dice rolls, consequences
    NARRATIVE = "narrative"                # Narrative summary displayed


class GamePhase(str, Enum):
    """Main game phase (PaxHistoria-style)

    Unlike TurnPhase (sequential steps), GamePhase represents the main loop:
    - ACCUMULATING: Player writes actions, they queue up
    - JUMPING: Jump Forward triggered, resolving all actions
    - PLAYBACK: Reading events one by one (Save/Intervene)
    """
    ACCUMULATING = "accumulating"   # Player accumulates actions in queue
    JUMPING = "jumping"             # Jump Forward in progress
    PLAYBACK = "playback"           # Reading events one by one


class ResolutionOutcome(str, Enum):
    """How a success happens (dice decides HOW, not IF)"""
    CLEAN_SUCCESS = "clean"        # Success without complications
    COSTLY_SUCCESS = "costly"      # Success but with costs
    FRAGILE_SUCCESS = "fragile"    # Success but creates dilemma
    SABOTAGED_SUCCESS = "sabotaged"  # Success but leak/opposition


# =============================================================================
# ACTION LOG (Fronts Vivants v2 - base sur les ACTIONS, pas les metriques)
# =============================================================================

class ActionLogEntry(BaseModel):
    """Une action loggee pour le systeme de Fronts Vivants.

    Chaque front derive de "preuves d'actions" (beats), pas de metriques.
    Le log capture tout: actions joueur, IA, evenements, TEST choices, aftershocks.

    Visibility:
    - "public": visible par tous (discours, blocus, mouvements de troupes)
    - "covert": operation secrete (KGB, CIA, sabotage)
    - "rumor": source inconnue, fiabilite incertaine
    """
    turn: int
    zone_id: str
    actor: str        # "usa" | "ussr" | "local" | "unknown"
    action_type: str  # "BLOCKADE", "SUMMIT", "COVERT_OP", "RUMOR", "TEST_CHOICE", etc.
    intensity: str    # "light" | "moderate" | "heavy"
    payload_fr: str   # Micro-phrase brute (la "preuve")
    visibility: str   # "public" | "covert" | "rumor"

    # Optional metadata
    source_event_id: Optional[str] = None  # Link to jump_event if applicable
    is_test_choice: bool = False           # True if this is a player TEST choice
    is_aftershock: bool = False            # True if this is an aftershock consequence


# =============================================================================
# DIPLOMACY VARIABLES
# =============================================================================

class DiplomacyProfile(BaseModel):
    """4 variables per interlocutor as per P4"""
    trust: int = Field(default=50, ge=0, le=100)      # Confidence in your commitments
    fear: int = Field(default=30, ge=0, le=100)       # Fear of your retaliation
    respect: int = Field(default=50, ge=0, le=100)    # Credibility of your word
    leverage: int = Field(default=0, ge=-100, le=100)  # Concrete power balance

    def get_negotiation_modifier(self) -> float:
        """Calculate overall negotiation effectiveness"""
        # High trust + respect = better deals
        # High fear + leverage = more concessions
        positive = (self.trust + self.respect) / 200
        pressure = (self.fear + max(0, self.leverage)) / 200
        return 0.5 + (positive * 0.3) + (pressure * 0.2)

    def update_from_action(self, action_type: str, success: bool) -> Dict[str, int]:
        """Update diplomacy variables based on action"""
        changes = {}

        if action_type == "threat":
            changes["fear"] = 10 if success else -15
            changes["trust"] = -5
        elif action_type == "concession":
            changes["trust"] = 10
            changes["fear"] = -10
            changes["respect"] = -5 if not success else 5
        elif action_type == "promise_kept":
            changes["trust"] = 15
            changes["respect"] = 10
        elif action_type == "promise_broken":
            changes["trust"] = -25
            changes["respect"] = -15
        elif action_type == "military_demo":
            changes["fear"] = 15
            changes["respect"] = 5 if success else -10
        elif action_type == "economic_aid":
            changes["trust"] = 5
            changes["leverage"] = 10
        elif action_type == "sanction":
            changes["fear"] = 5
            changes["trust"] = -10
            changes["leverage"] = 15 if success else -5

        # Apply changes
        for var, delta in changes.items():
            current = getattr(self, var)
            if var == "leverage":
                setattr(self, var, max(-100, min(100, current + delta)))
            else:
                setattr(self, var, max(0, min(100, current + delta)))

        return changes


# =============================================================================
# ZONE STATE (12 zones)
# =============================================================================

class NarrativeZone(BaseModel):
    """Zone state for narrative mode - 12 strategic zones"""
    id: str
    name_fr: str
    name_en: str

    # Influence (0-100, visible)
    influence_us: int = Field(default=50, ge=0, le=100)
    influence_ussr: int = Field(default=50, ge=0, le=100)

    # Control (0-100, partially hidden)
    control_us: int = Field(default=30, ge=0, le=100)
    control_ussr: int = Field(default=30, ge=0, le=100)

    # Zone stability (0-100, partial)
    stability: int = Field(default=50, ge=0, le=100)

    # Strategic value (1-10, fixed)
    strategic_value: int = Field(default=5, ge=1, le=10)

    # Active crisis in zone
    has_crisis: bool = False
    crisis_type: Optional[str] = None
    crisis_intensity: int = 0

    def get_dominant_power(self) -> str:
        """Returns 'US', 'USSR', or 'contested'"""
        diff = self.influence_us - self.influence_ussr
        if diff > 15:
            return "US"
        elif diff < -15:
            return "USSR"
        return "contested"

    def is_controlled_by(self, power: str) -> bool:
        """Check if power has significant control"""
        if power == "US":
            return self.control_us >= 60
        elif power == "USSR":
            return self.control_ussr >= 60
        return False

    def get_instability_risk(self) -> str:
        """Get instability risk level"""
        # P2: High influence + low control = explosion risk
        us_gap = max(0, self.influence_us - self.control_us)
        ussr_gap = max(0, self.influence_ussr - self.control_ussr)
        max_gap = max(us_gap, ussr_gap)

        if max_gap > 40 and self.stability < 40:
            return "critical"
        elif max_gap > 30 or self.stability < 50:
            return "high"
        elif max_gap > 15 or self.stability < 65:
            return "medium"
        return "low"

    def get_effective_importance(self, all_zones: Optional[Dict[str, "NarrativeZone"]] = None) -> int:
        """
        Dynamic importance based on current context.

        Cuba 1959 = Tier 4 (low base), Cuba 1962 (missiles) = Tier 1 (crisis bonus!)

        Bonuses:
        - Active crisis: +1 to +5 based on intensity
        - Low stability (<30): +1
        - Hotly contested (control diff <20): +1
        - Domino effect from adjacent crises: +1 to +3
        """
        importance = self.strategic_value

        # Crisis active = high importance
        if self.has_crisis:
            crisis_bonus = self.crisis_intensity // 20  # 0-5 bonus
            importance = min(10, importance + crisis_bonus)

        # Unstable zone = more risk = more important
        if self.stability < 30:
            importance = min(10, importance + 1)

        # Contested (close to 50/50) = strategic
        control_diff = abs(self.control_us - self.control_ussr)
        if control_diff < 20:  # Very contested
            importance = min(10, importance + 1)

        # Domino effect from adjacent zones (Option 2)
        if all_zones:
            from engine.domino_effects import calculate_domino_bonus
            domino_bonus = calculate_domino_bonus(self.id, all_zones)
            importance = min(10, importance + domino_bonus)

        return importance


# =============================================================================
# PLAYER STATE
# =============================================================================

class PlayerState(BaseModel):
    """Player (US) variables"""
    country_id: str = "USA"

    # Core player resources (visible)
    political_capital: int = Field(default=70, ge=0, le=100)
    domestic_stability: int = Field(default=65, ge=0, le=100)
    international_reputation: int = Field(default=70, ge=0, le=100)

    # Intel exposure (partial visibility)
    intel_exposure: int = Field(default=20, ge=0, le=100)

    # Diplomatic profiles with key actors
    diplomacy: Dict[str, DiplomacyProfile] = Field(default_factory=dict)

    # Turn tracking
    current_turn: int = 1
    actions_this_turn: List[str] = Field(default_factory=list)

    def get_action_capacity(self) -> int:
        """How many actions player can take (P1: no budget, but consequences limit)"""
        # Low capital = fewer risky options
        if self.political_capital < 20:
            return 1
        elif self.political_capital < 40:
            return 2
        elif self.political_capital < 70:
            return 3
        return 4  # High capital = more freedom

    def can_afford_action(self, action_cost: int) -> bool:
        """Check if player has enough capital for action"""
        return self.political_capital >= action_cost

    def spend_capital(self, amount: int) -> bool:
        """Spend political capital"""
        if self.political_capital >= amount:
            self.political_capital = max(0, self.political_capital - amount)
            return True
        return False

    def get_diplomacy_with(self, actor_id: str) -> DiplomacyProfile:
        """Get or create diplomacy profile for an actor"""
        if actor_id not in self.diplomacy:
            self.diplomacy[actor_id] = DiplomacyProfile()
        return self.diplomacy[actor_id]


# =============================================================================
# ADVERSARY STATE (USSR)
# =============================================================================

class AdversaryState(BaseModel):
    """Adversary (USSR) AI state - P5: Doctrine + Constraints"""
    country_id: str = "USSR"

    # Doctrine (hidden)
    doctrine: AdversaryDoctrine = AdversaryDoctrine.EXPANSION

    # Internal pressures (hidden, P5)
    pressure_army: int = Field(default=50, ge=0, le=100)    # Military failure pressure
    pressure_party: int = Field(default=50, ge=0, le=100)   # Party pressure
    pressure_economy: int = Field(default=40, ge=0, le=100) # Economic constraints

    # Personality (hidden)
    impulsivity: int = Field(default=60, ge=0, le=100)     # Khrushchev = high
    risk_tolerance: int = Field(default=50, ge=0, le=100)

    # Strategic goals (hidden)
    priority_zones: List[str] = Field(default_factory=list)
    forbidden_concessions: List[str] = Field(default_factory=list)

    # Diplomatic profiles
    diplomacy: Dict[str, DiplomacyProfile] = Field(default_factory=dict)

    def get_total_pressure(self) -> int:
        """Get total internal pressure"""
        return (self.pressure_army + self.pressure_party + self.pressure_economy) // 3

    def can_concede(self, topic: str) -> bool:
        """Check if adversary can concede on a topic (P5: interdits)"""
        total_pressure = self.get_total_pressure()
        # High pressure = cannot show weakness
        if total_pressure > 70 and topic in self.forbidden_concessions:
            return False
        return True

    def get_aggression_modifier(self) -> float:
        """How aggressive is the AI this turn"""
        base = 1.0

        # Doctrine modifier
        if self.doctrine == AdversaryDoctrine.EXPANSION:
            base += 0.3
        elif self.doctrine == AdversaryDoctrine.DESTABILIZATION:
            base += 0.2
        elif self.doctrine == AdversaryDoctrine.DETENTE:
            base -= 0.3
        elif self.doctrine == AdversaryDoctrine.CONSOLIDATION:
            base -= 0.2

        # Pressure modifier
        pressure = self.get_total_pressure()
        if pressure > 70:
            base += 0.2  # Desperate = aggressive
        elif pressure < 30:
            base -= 0.1  # Comfortable = cautious

        # Impulsivity
        base += (self.impulsivity - 50) / 200

        return max(0.3, min(1.7, base))

    def update_doctrine_from_situation(self, world_tension: int, player_strength: int):
        """Adapt doctrine based on situation"""
        pressure = self.get_total_pressure()

        if pressure > 80:
            # High pressure: consolidate or lash out
            if self.risk_tolerance > 60:
                self.doctrine = AdversaryDoctrine.ARMS_RACE
            else:
                self.doctrine = AdversaryDoctrine.CONSOLIDATION
        elif world_tension > 70:
            # High tension: seek detente or destabilize
            if player_strength > 60:
                self.doctrine = AdversaryDoctrine.DETENTE
            else:
                self.doctrine = AdversaryDoctrine.DESTABILIZATION
        elif player_strength < 40:
            # Player weak: expand
            self.doctrine = AdversaryDoctrine.EXPANSION
        # Otherwise keep current doctrine


# =============================================================================
# INTEL STATE (P3: Intel has a cost)
# =============================================================================

class IntelReport(BaseModel):
    """Intelligence report on a topic"""
    topic: str
    zone_id: Optional[str] = None
    actor_id: Optional[str] = None

    # What we know
    content: str
    content_fr: str

    # Reliability (P3: can be disinformation)
    reliability: str = "uncertain"  # certain, likely, uncertain, rumor
    is_disinformation: bool = False  # True reality, player doesn't know

    # Cost of collection
    exposure_cost: int = 0  # Added to player's intel_exposure

    turn_collected: int = 0

    def get_actual_reliability(self) -> float:
        """Get true reliability (hidden from player)"""
        if self.is_disinformation:
            return 0.0

        reliability_map = {
            "certain": 0.95,
            "likely": 0.75,
            "uncertain": 0.50,
            "rumor": 0.30
        }
        return reliability_map.get(self.reliability, 0.5)


class IntelState(BaseModel):
    """Intel system state"""
    collected_reports: List[IntelReport] = Field(default_factory=list)

    # Known intel levels per target (0-100)
    intel_levels: Dict[str, int] = Field(default_factory=dict)

    # Active collection operations (can be detected)
    active_ops: List[str] = Field(default_factory=list)

    def get_intel_on(self, target: str) -> int:
        """Get intel level on a target"""
        return self.intel_levels.get(target, 0)

    def collect_intel(self, target: str, depth: str = "surface") -> int:
        """Start intel collection, returns exposure risk"""
        depth_costs = {
            "surface": 5,
            "detailed": 15,
            "deep": 30
        }
        return depth_costs.get(depth, 10)


# =============================================================================
# PENDING ACTION
# =============================================================================

class PendingAction(BaseModel):
    """Action waiting for confirmation"""
    id: str
    intention_type: str
    intention_id: str

    target_zone: Optional[str] = None
    target_actor: Optional[str] = None

    description_fr: str

    # Costs and risks
    political_cost: int = 0
    risk_level: str = "low"  # low, medium, high, extreme

    # Predicted consequences (what player sees)
    predicted_effects: Dict[str, Any] = Field(default_factory=dict)

    # Whether player confirmed
    confirmed: bool = False


# =============================================================================
# NARRATIVE WORLD STATE
# =============================================================================

# Nombre de mois par jump (accelere le temps pour rendre le jeu jouable)
MONTHS_PER_JUMP = 3  # 1 jump = 1 trimestre

class NarrativeWorldState(BaseModel):
    """Complete state for Historia Narrative mode (PaxHistoria-style)

    This is the main game state that tracks everything for the narrative game.

    PaxHistoria model:
    - Actions accumulate in player_action_queue (not immediately executed)
    - Adversary plans in parallel (adversary_action_queue, hidden)
    - Jump Forward resolves all actions + generates events
    - Events read one-by-one in playback mode
    """
    # Timeline
    year: int = 1962
    month: int = 10  # October 1962 - Cuban Missile Crisis
    turn: int = 1

    # Game phase (PaxHistoria-style)
    game_phase: GamePhase = GamePhase.ACCUMULATING
    current_phase: TurnPhase = TurnPhase.PLAYER_INPUT  # Legacy, kept for compat

    # Global tension (visible)
    defcon: int = Field(default=3, ge=1, le=5)  # 5=peace, 1=war imminent
    world_tension: int = Field(default=65, ge=0, le=100)

    # Player and Adversary
    player: PlayerState = Field(default_factory=PlayerState)
    adversary: AdversaryState = Field(default_factory=AdversaryState)

    # Zones (12)
    zones: Dict[str, NarrativeZone] = Field(default_factory=dict)

    # Intel system
    intel: IntelState = Field(default_factory=IntelState)

    # =========================================================================
    # PAXHISTORIA: ACTION QUEUES
    # =========================================================================

    # Player action queue (accumulated before Jump Forward)
    # Stored as list of dicts for JSON serialization, converted to ActionQueue when needed
    player_action_queue_data: List[Dict[str, Any]] = Field(default_factory=list)
    player_reserved_capital: int = 0  # Capital reserved by queued actions

    # Adversary action queue (hidden from player, revealed at jump)
    adversary_action_queue: List[Dict[str, Any]] = Field(default_factory=list)
    adversary_planned: bool = False  # Has adversary planned for this accumulation?

    # =========================================================================
    # PAXHISTORIA: JUMP FORWARD STATE
    # =========================================================================

    # Jump configuration
    jump_duration: Optional[str] = None  # "week", "month", "quarter", "year", "next_event"
    jump_target_date: Optional[str] = None  # ISO date if jumping to specific date

    # Events generated by jump (for playback)
    jump_events: List[Dict[str, Any]] = Field(default_factory=list)
    current_event_index: int = 0
    saved_at_event: Optional[int] = None  # If player saved during playback

    # =========================================================================
    # LEGACY (kept for compatibility)
    # =========================================================================

    # Pending actions for current turn (legacy turn-by-turn)
    pending_actions: List[PendingAction] = Field(default_factory=list)

    # Turn history
    turn_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Events queue (legacy)
    events_queue: List[Dict[str, Any]] = Field(default_factory=list)

    # Game end conditions
    game_over: bool = False
    victory: bool = False
    end_reason: Optional[str] = None

    # =========================================================================
    # SILENCE MECHANICS (inactivite du joueur)
    # =========================================================================
    silence_state_data: Dict[str, Any] = Field(default_factory=dict)

    # =========================================================================
    # ACTION LOG (Fronts Vivants v2)
    # =========================================================================
    # Log de toutes les actions (joueur + IA + events) pour alimenter les Fronts
    action_log: List[ActionLogEntry] = Field(default_factory=list)

    def advance_month(self):
        """Advance calendar by MONTHS_PER_JUMP (default: 3 = trimestre)"""
        self.month += MONTHS_PER_JUMP
        while self.month > 12:
            self.month -= 12
            self.year += 1

    def next_turn(self):
        """Start next turn"""
        self.turn += 1
        self.advance_month()
        self.pending_actions = []
        self.current_phase = TurnPhase.PLAYER_INPUT
        self.player.actions_this_turn = []

    def get_date_display(self, lang: str = "fr") -> str:
        """Get formatted date"""
        months_fr = [
            "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"
        ]
        months_en = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        if lang == "fr":
            return f"{months_fr[self.month - 1]} {self.year}"
        return f"{months_en[self.month - 1]} {self.year}"

    def check_victory_conditions(self) -> Optional[str]:
        """Check for victory/defeat conditions"""
        # DEFCON 1 = Apocalypse
        if self.defcon <= 1:
            self.game_over = True
            self.victory = False
            self.end_reason = "apocalypse"
            return "apocalypse"

        # Player collapse
        if self.player.domestic_stability < 20:
            self.game_over = True
            self.victory = False
            self.end_reason = "coup_etat"
            return "coup_etat"

        # VICTOIRE LOCALE: Crise resolue (Cuba)
        # Condition: crise active desamorcee + tension mondiale sous controle
        cuba = self.zones.get("central_america")
        if cuba and cuba.has_crisis and cuba.crisis_type == "missiles_cuba":
            # Crise resolue si intensite basse ET tension mondiale acceptable
            if cuba.crisis_intensity <= 25 and self.world_tension <= 50:
                self.game_over = True
                self.victory = True
                self.end_reason = "crisis_resolved"
                return "crisis_resolved"

        # Count US influence globally
        us_influence = sum(z.influence_us for z in self.zones.values()) / len(self.zones) if self.zones else 50
        ussr_influence = sum(z.influence_ussr for z in self.zones.values()) / len(self.zones) if self.zones else 50

        # Victory by domination (70%+ for 3 turns)
        if us_influence >= 70 and self.turn >= 15:
            self.game_over = True
            self.victory = True
            self.end_reason = "domination"
            return "domination"

        # Adversary collapse
        if self.adversary.pressure_economy > 90:
            self.game_over = True
            self.victory = True
            self.end_reason = "adversary_collapse"
            return "adversary_collapse"

        # Survival victory (reach 1991)
        if self.year >= 1991:
            if us_influence > ussr_influence:
                self.game_over = True
                self.victory = True
                self.end_reason = "survival"
                return "survival"
            else:
                self.game_over = True
                self.victory = False
                self.end_reason = "defeat_honorable"
                return "defeat_honorable"

        return None

    def get_visible_state(self) -> Dict[str, Any]:
        """Get state visible to player (with fog of war applied)"""
        queue = self.get_action_queue()

        visible = {
            "year": self.year,
            "month": self.month,
            "turn": self.turn,
            "date_display": self.get_date_display("fr"),
            "current_phase": self.current_phase.value,
            "defcon": self.defcon,
            "world_tension": self.world_tension,

            # PaxHistoria: Game phase
            "game_phase": self.game_phase.value,

            # Player stats (all visible)
            "player": {
                "political_capital": self.player.political_capital,
                "domestic_stability": self.player.domestic_stability,
                "international_reputation": self.player.international_reputation,
                "intel_exposure": self.player.intel_exposure,
                "action_capacity": self.player.get_action_capacity(),
                "available_capital": self.player.political_capital - self.player_reserved_capital,
            },

            # Adversary (only partial based on intel)
            "adversary": self._get_adversary_visible(),

            # Zones (with fog of war)
            "zones": {
                zone_id: self._get_zone_visible(zone)
                for zone_id, zone in self.zones.items()
            },

            # PaxHistoria: Action queue
            "action_queue": queue.to_dict(),

            # Legacy: Pending actions (kept for compatibility)
            "pending_actions": [
                {
                    "id": a.id,
                    "intention_type": a.intention_type,
                    "description_fr": a.description_fr,
                    "political_cost": a.political_cost,
                    "risk_level": a.risk_level,
                    "predicted_effects": a.predicted_effects,
                    "confirmed": a.confirmed,
                }
                for a in self.pending_actions
            ],

            # PaxHistoria: Playback state (if in playback)
            "playback": self.get_playback_state() if self.game_phase == GamePhase.PLAYBACK else None,

            # Game state
            "game_over": self.game_over,
            "victory": self.victory,
            "end_reason": self.end_reason,
        }

        return visible

    def _get_adversary_visible(self) -> Dict[str, Any]:
        """Get adversary info visible based on intel level"""
        intel_level = self.intel.get_intel_on("USSR")

        result = {
            "known": intel_level >= 20
        }

        if intel_level >= 40:
            # Partial: economy estimate
            result["economy_pressure"] = "high" if self.adversary.pressure_economy > 60 else "moderate" if self.adversary.pressure_economy > 30 else "low"

        if intel_level >= 60:
            # Good: doctrine hint
            if self.adversary.doctrine == AdversaryDoctrine.EXPANSION:
                result["doctrine_hint"] = "aggressive"
            elif self.adversary.doctrine == AdversaryDoctrine.DETENTE:
                result["doctrine_hint"] = "conciliatory"
            else:
                result["doctrine_hint"] = "unknown"

        if intel_level >= 80:
            # Very good: pressure levels
            result["internal_pressure"] = self.adversary.get_total_pressure()

        return result

    def _get_zone_visible(self, zone: NarrativeZone) -> Dict[str, Any]:
        """Get zone info visible to player"""
        return {
            "id": zone.id,
            "name_fr": zone.name_fr,
            "influence_us": zone.influence_us,
            "influence_ussr": zone.influence_ussr,
            "control_us": zone.control_us,  # Visible for own control
            "control_ussr_estimate": self._estimate_control(zone, "USSR"),
            "stability": zone.stability,
            "strategic_value": zone.strategic_value,
            "dominant": zone.get_dominant_power(),
            "instability_risk": zone.get_instability_risk(),
            "has_crisis": zone.has_crisis,
            "crisis_type": zone.crisis_type if zone.has_crisis else None,
        }

    def _estimate_control(self, zone: NarrativeZone, power: str) -> str:
        """Estimate enemy control based on intel"""
        intel_level = self.intel.get_intel_on(f"zone_{zone.id}")
        actual = zone.control_ussr if power == "USSR" else zone.control_us

        if intel_level < 40:
            return "unknown"
        elif intel_level < 70:
            # Rough estimate
            if actual > 60:
                return "high"
            elif actual > 30:
                return "moderate"
            return "low"
        else:
            # Good estimate with range
            return f"{max(0, actual - 10)}-{min(100, actual + 10)}"

    # =========================================================================
    # PAXHISTORIA: ACTION QUEUE METHODS
    # =========================================================================

    def get_action_queue(self) -> "ActionQueue":
        """Get ActionQueue object from stored data"""
        from engine.action_queue import ActionQueue
        queue = ActionQueue.from_dict({
            "actions": self.player_action_queue_data,
            "total_reserved_capital": self.player_reserved_capital,
            "available_capital": self.player.political_capital,
        })
        return queue

    def save_action_queue(self, queue: "ActionQueue"):
        """Save ActionQueue object back to state"""
        self.player_action_queue_data = [a.model_dump() for a in queue.actions]
        self.player_reserved_capital = queue.total_reserved_capital

    def queue_action(self, action_data: Dict[str, Any]) -> tuple[bool, str]:
        """Add action to queue (PaxHistoria-style)

        Returns (success, message)
        """
        from engine.action_queue import ActionQueue, QueuedAction

        queue = self.get_action_queue()
        action = QueuedAction(**action_data)
        success, message = queue.add(action)

        if success:
            self.save_action_queue(queue)
            # Trigger adversary planning on first action
            if not self.adversary_planned and len(queue.actions) == 1:
                self._trigger_adversary_planning()

        return success, message

    def remove_queued_action(self, action_id: str) -> tuple[bool, str]:
        """Remove action from queue

        Returns (success, message)
        """
        queue = self.get_action_queue()
        success, message = queue.remove(action_id)

        if success:
            self.save_action_queue(queue)

        return success, message

    def clear_action_queue(self):
        """Clear all queued actions"""
        self.player_action_queue_data = []
        self.player_reserved_capital = 0

    def get_queue_preview(self) -> Dict[str, Any]:
        """Get preview of what would happen if Jump Forward is triggered now"""
        queue = self.get_action_queue()
        return {
            "queue_summary": queue.get_queue_summary(),
            "predicted_effects": queue.calculate_preview_effects(),
            "available_capital": self.player.political_capital - self.player_reserved_capital,
        }

    def _trigger_adversary_planning(self):
        """Trigger adversary to plan their actions (called on first player action)"""
        # Will be implemented in adversary_ai.py
        # For now, just mark that planning is needed
        self.adversary_planned = False
        logger.info("Adversary planning triggered")

    # =========================================================================
    # PAXHISTORIA: JUMP FORWARD METHODS
    # =========================================================================

    def start_jump(self, duration: str):
        """Start Jump Forward process"""
        self.game_phase = GamePhase.JUMPING
        self.jump_duration = duration
        self.jump_events = []
        self.current_event_index = 0
        logger.info(f"Starting Jump Forward: {duration}")

    def start_playback(self, events: List[Dict[str, Any]]):
        """Start event playback after jump resolution"""
        self.game_phase = GamePhase.PLAYBACK
        self.jump_events = events
        self.current_event_index = 0
        logger.info(f"Starting playback of {len(events)} events")

    def next_event(self) -> Optional[Dict[str, Any]]:
        """Get next event in playback"""
        if self.current_event_index < len(self.jump_events):
            event = self.jump_events[self.current_event_index]
            self.current_event_index += 1
            return event
        return None

    def save_here(self):
        """Save game at current event during playback"""
        self.saved_at_event = self.current_event_index
        logger.info(f"Game saved at event {self.current_event_index}")

    def intervene(self):
        """Stop playback to allow player intervention"""
        self.game_phase = GamePhase.ACCUMULATING
        # Clear remaining events
        remaining = self.jump_events[self.current_event_index:]
        self.jump_events = self.jump_events[:self.current_event_index]
        logger.info(f"Player intervened, {len(remaining)} events cancelled")
        return remaining

    def end_playback(self):
        """End playback and return to accumulation phase"""
        self.game_phase = GamePhase.ACCUMULATING
        self.jump_events = []
        self.current_event_index = 0
        self.jump_duration = None
        self.clear_action_queue()
        self.adversary_action_queue = []
        self.adversary_planned = False
        self.turn += 1
        logger.info("Playback ended, returning to accumulation")

    def get_playback_state(self) -> Dict[str, Any]:
        """Get current playback state"""
        return {
            "phase": self.game_phase.value,
            "total_events": len(self.jump_events),
            "current_index": self.current_event_index,
            "current_event": self.jump_events[self.current_event_index] if self.current_event_index < len(self.jump_events) else None,
            "remaining": len(self.jump_events) - self.current_event_index,
            "saved_at": self.saved_at_event,
        }

    # =========================================================================
    # SILENCE MECHANICS METHODS
    # =========================================================================

    def get_silence_state(self) -> "SilenceState":
        """Get SilenceState object from stored data"""
        from engine.silence_mechanics import SilenceState
        if not self.silence_state_data:
            return SilenceState()
        return SilenceState(**self.silence_state_data)

    def save_silence_state(self, silence_state: "SilenceState"):
        """Save SilenceState back to state data"""
        from dataclasses import asdict
        self.silence_state_data = asdict(silence_state)

    def check_silence_consequences(self, action_count: int, ignored_dossier_ids: List[str] = None):
        """Check and apply silence consequences after a jump.

        Returns list of SilenceEvent if any triggers fired.
        """
        from engine.silence_mechanics import (
            check_silence_triggers,
            update_silence_state,
            apply_silence_effects,
        )

        # Get current silence state
        silence_state = self.get_silence_state()

        # Update silence tracking
        update_silence_state(
            silence_state,
            action_count=action_count,
            ignored_dossier_ids=ignored_dossier_ids or [],
            current_turn=self.turn
        )

        # Check if any triggers fire
        is_ussr = self.player.country_id == "USSR"
        events = check_silence_triggers(
            silence_state=silence_state,
            world_state=self,
            is_ussr=is_ussr
        )

        # Apply effects if any events triggered
        if events:
            narratives = apply_silence_effects(self, events)
            logger.info(f"Silence mechanics: {len(events)} events triggered")

        # Save updated silence state
        self.save_silence_state(silence_state)

        return events

    # =========================================================================
    # ACTION LOG METHODS (Fronts Vivants v2)
    # =========================================================================

    def log_action(
        self,
        zone_id: str,
        actor: str,
        action_type: str,
        intensity: str,
        payload_fr: str,
        visibility: str = "public",
        source_event_id: Optional[str] = None,
        is_test_choice: bool = False,
        is_aftershock: bool = False,
    ) -> ActionLogEntry:
        """Log une action pour le systeme de Fronts Vivants.

        Appelé par:
        - jump_engine.py lors de la resolution des actions joueur/IA
        - event generation lors des evenements mondiaux
        - TEST choices lors des choix du joueur en playback
        - aftershock generation apres les TEST
        """
        entry = ActionLogEntry(
            turn=self.turn,
            zone_id=zone_id,
            actor=actor,
            action_type=action_type,
            intensity=intensity,
            payload_fr=payload_fr,
            visibility=visibility,
            source_event_id=source_event_id,
            is_test_choice=is_test_choice,
            is_aftershock=is_aftershock,
        )
        self.action_log.append(entry)
        logger.debug(f"Action logged: {action_type} by {actor} in {zone_id}")
        return entry

    def get_recent_actions(
        self,
        zone_id: Optional[str] = None,
        lookback_turns: int = 3,
        actor: Optional[str] = None,
    ) -> List[ActionLogEntry]:
        """Recupere les actions recentes pour une zone.

        Utilise par front_state.py pour calculer:
        - dominant_mode (soft/hard/covert/standoff)
        - last beat
        - tension cadence
        """
        min_turn = max(1, self.turn - lookback_turns + 1)
        results = []
        for entry in self.action_log:
            if entry.turn < min_turn:
                continue
            if zone_id and entry.zone_id != zone_id:
                continue
            if actor and entry.actor != actor:
                continue
            results.append(entry)
        return results

    def get_last_beat(self, zone_id: str) -> Optional[ActionLogEntry]:
        """Recupere la derniere action significative pour une zone.

        C'est le 'beat' qui s'affichera dans le FrontWall.
        """
        for entry in reversed(self.action_log):
            if entry.zone_id == zone_id:
                return entry
        return None

    def get_zones_with_activity(self, lookback_turns: int = 2) -> List[str]:
        """Recupere les zones avec activite recente (spotlight).

        Utilise pour selectionner quels fronts afficher dans le FrontWall.
        """
        min_turn = max(1, self.turn - lookback_turns + 1)
        active_zones = set()
        for entry in self.action_log:
            if entry.turn >= min_turn:
                active_zones.add(entry.zone_id)
        return list(active_zones)


def create_initial_state() -> NarrativeWorldState:
    """Create initial game state for Cuban Missile Crisis scenario"""
    state = NarrativeWorldState()

    # Initialize 12 zones
    zones_data = [
        ("europe_west", "Europe de l'Ouest", "Western Europe", 75, 15, 80, 10, 80, 10),
        ("europe_east", "Europe de l'Est", "Eastern Europe", 10, 85, 5, 90, 50, 8),
        ("central_america", "Amerique Centrale", "Central America", 60, 40, 40, 50, 45, 9),
        ("south_america", "Amerique du Sud", "South America", 55, 30, 35, 20, 55, 6),
        ("middle_east", "Moyen-Orient", "Middle East", 40, 35, 30, 25, 40, 10),
        ("north_africa", "Afrique du Nord", "North Africa", 35, 40, 20, 35, 50, 5),
        ("sub_sahara", "Afrique Sub-saharienne", "Sub-Saharan Africa", 30, 35, 15, 25, 45, 4),
        ("southeast_asia", "Asie du Sud-Est", "Southeast Asia", 35, 50, 30, 40, 35, 7),
        ("south_asia", "Asie du Sud", "South Asia", 40, 30, 25, 20, 50, 6),
        ("far_east", "Extreme-Orient", "Far East", 55, 45, 50, 35, 60, 8),
        ("turkey_greece", "Turquie/Grece", "Turkey/Greece", 70, 20, 65, 15, 55, 9),
        ("scandinavia", "Scandinavie", "Scandinavia", 65, 25, 50, 15, 80, 5),
    ]

    for z_id, name_fr, name_en, inf_us, inf_ussr, ctl_us, ctl_ussr, stab, value in zones_data:
        state.zones[z_id] = NarrativeZone(
            id=z_id,
            name_fr=name_fr,
            name_en=name_en,
            influence_us=inf_us,
            influence_ussr=inf_ussr,
            control_us=ctl_us,
            control_ussr=ctl_ussr,
            stability=stab,
            strategic_value=value,
        )

    # Set Cuba crisis
    state.zones["central_america"].has_crisis = True
    state.zones["central_america"].crisis_type = "missiles_cuba"
    state.zones["central_america"].crisis_intensity = 80

    # Initialize adversary
    state.adversary.doctrine = AdversaryDoctrine.EXPANSION
    state.adversary.impulsivity = 70  # Khrushchev
    state.adversary.priority_zones = ["central_america", "europe_east", "middle_east"]
    state.adversary.forbidden_concessions = ["berlin", "cuba_missiles"]

    # Initialize player diplomacy with USSR
    state.player.diplomacy["USSR"] = DiplomacyProfile(
        trust=30,
        fear=60,
        respect=55,
        leverage=-10
    )

    # Initialize adversary diplomacy with USA
    state.adversary.diplomacy["USA"] = DiplomacyProfile(
        trust=25,
        fear=65,
        respect=60,
        leverage=15
    )

    # Initial intel levels
    state.intel.intel_levels = {
        "USSR": 45,
        "zone_europe_west": 90,
        "zone_europe_east": 40,
        "zone_central_america": 70,
        "zone_middle_east": 55,
    }

    logger.info("Created initial NarrativeWorldState for October 1962")
    return state
