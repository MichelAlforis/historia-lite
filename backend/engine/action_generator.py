"""Action Generator for Historia Narrative

Transforms parsed intentions into concrete actions with:
- Costs
- Risk levels
- Predicted consequences
- Resolution requirements

Based on Plan: A1 - Separation Intention -> Action
"""
import logging
import random
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field

from .narrative_state import (
    NarrativeWorldState,
    PendingAction,
    ResolutionOutcome,
    NarrativeZone,
    DiplomacyProfile,
)
from .intent_parser import (
    ParsedIntention,
    IntentionType,
    IntentionCategory,
    INTENTION_METADATA,
)
from .action_cost_calculator import (
    calculate_action_cost,
    calculate_action_risk,
    calculate_action_cost_breakdown,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ACTION EFFECTS
# =============================================================================

class EffectType(str, Enum):
    """Types of effects an action can have"""
    INFLUENCE = "influence"
    CONTROL = "control"
    STABILITY = "stability"
    DIPLOMACY = "diplomacy"
    DEFCON = "defcon"
    POLITICAL_CAPITAL = "political_capital"
    REPUTATION = "reputation"
    INTEL = "intel"
    ADVERSARY = "adversary"


class ActionEffect(BaseModel):
    """A single effect of an action"""
    effect_type: EffectType
    target: str  # zone_id, country_id, or "player", "adversary"
    variable: str  # specific variable affected
    delta: int  # change amount
    conditional: bool = False  # requires successful resolution
    description_fr: str = ""


class GeneratedAction(BaseModel):
    """A concrete action generated from an intention"""
    id: str
    intention_id: str
    intention_type: IntentionType

    # Target
    zone_id: Optional[str] = None
    country_id: Optional[str] = None
    topic: Optional[str] = None

    # Display
    name_fr: str
    description_fr: str

    # Costs
    political_cost: int = 0

    # Risk assessment (P6: dice decides HOW, not IF)
    risk_level: str = "low"  # low, medium, high, extreme
    success_guaranteed: bool = True  # Most actions succeed, but HOW varies
    base_success_rate: float = 0.9

    # Effects (what happens if action proceeds)
    effects: List[ActionEffect] = Field(default_factory=list)

    # Predicted consequences (shown to player)
    predicted_effects: Dict[str, Any] = Field(default_factory=dict)

    # Resolution info
    resolution_type: str = "automatic"  # automatic, dice, negotiation
    possible_outcomes: List[str] = Field(default_factory=list)

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    def to_pending_action(self) -> PendingAction:
        """Convert to PendingAction for state"""
        return PendingAction(
            id=self.id,
            intention_type=self.intention_type.value,
            intention_id=self.intention_id,
            target_zone=self.zone_id,
            target_actor=self.country_id,
            description_fr=self.description_fr,
            political_cost=self.political_cost,
            risk_level=self.risk_level,
            predicted_effects=self.predicted_effects,
            confirmed=False,
        )


# =============================================================================
# ACTION GENERATOR
# =============================================================================

class ActionGenerator:
    """Generates concrete actions from intentions"""

    def __init__(self):
        self._action_id_counter = 0

    def _next_id(self) -> str:
        """Generate unique action ID"""
        self._action_id_counter += 1
        return f"action_{self._action_id_counter}"

    def _calculate_dynamic_cost(
        self,
        intention_type: IntentionType,
        state: NarrativeWorldState,
        zone_id: Optional[str] = None,
    ) -> int:
        """Calculate dynamic cost based on context.

        Attacking China is NOT the same as influencing Belgium!
        """
        zone = state.zones.get(zone_id) if zone_id else None
        return calculate_action_cost(
            intention_type=intention_type.value,
            zone=zone,
            defcon=state.defcon,
            world_tension=state.world_tension,
        )

    def _calculate_dynamic_risk(
        self,
        intention_type: IntentionType,
        state: NarrativeWorldState,
        zone_id: Optional[str] = None,
    ) -> str:
        """Calculate dynamic risk based on context."""
        zone = state.zones.get(zone_id) if zone_id else None
        return calculate_action_risk(
            intention_type=intention_type.value,
            zone=zone,
            defcon=state.defcon,
            world_tension=state.world_tension,
        )

    def generate(
        self,
        intention: ParsedIntention,
        state: NarrativeWorldState
    ) -> GeneratedAction:
        """Generate a concrete action from an intention"""

        # Route to specific generator
        generators = {
            # Diplomacy
            IntentionType.DIPLO_ALLIANCE: self._gen_alliance,
            IntentionType.DIPLO_THREAT: self._gen_threat,
            IntentionType.DIPLO_NEGOTIATE: self._gen_negotiate,
            IntentionType.DIPLO_CONCEDE: self._gen_concede,
            IntentionType.DIPLO_SANCTION: self._gen_sanction,
            IntentionType.DIPLO_SUMMIT: self._gen_summit,
            IntentionType.DIPLO_BACKCHANNEL: self._gen_backchannel,

            # Military
            IntentionType.MIL_REINFORCE: self._gen_reinforce,
            IntentionType.MIL_WITHDRAW: self._gen_withdraw,
            IntentionType.MIL_DEMO: self._gen_demo,
            IntentionType.MIL_PROXY: self._gen_proxy,
            IntentionType.MIL_BLOCKADE: self._gen_blockade,
            IntentionType.MIL_BASE: self._gen_base,

            # Covert
            IntentionType.COV_DESTAB: self._gen_destab,
            IntentionType.COV_COUP: self._gen_coup,
            IntentionType.COV_SABOTAGE: self._gen_sabotage,
            IntentionType.COV_ASSASSIN: self._gen_assassin,
            IntentionType.COV_PROPAGANDA: self._gen_propaganda,

            # Intel
            IntentionType.INTEL_COLLECT: self._gen_intel_collect,
            IntentionType.INTEL_VERIFY: self._gen_intel_verify,
            IntentionType.INTEL_COUNTER: self._gen_intel_counter,
            IntentionType.INTEL_DISINFO: self._gen_intel_disinfo,

            # Economic
            IntentionType.ECO_AID: self._gen_eco_aid,
            IntentionType.ECO_TRADE: self._gen_eco_trade,
            IntentionType.ECO_EMBARGO: self._gen_eco_embargo,
            IntentionType.ECO_INVEST: self._gen_eco_invest,

            # Domestic
            IntentionType.DOM_SPEECH: self._gen_dom_speech,
            IntentionType.DOM_REFORM: self._gen_dom_reform,
            IntentionType.DOM_REPRESS: self._gen_dom_repress,
            IntentionType.DOM_ELECTION: self._gen_dom_election,
        }

        generator = generators.get(intention.type, self._gen_default)
        action = generator(intention, state)

        # Add warnings based on state
        action.warnings.extend(self._check_warnings(action, state))

        return action

    def generate_all(
        self,
        intentions: List[ParsedIntention],
        state: NarrativeWorldState
    ) -> List[GeneratedAction]:
        """Generate actions for all intentions"""
        return [self.generate(intention, state) for intention in intentions]

    # =========================================================================
    # DIPLOMACY GENERATORS
    # =========================================================================

    def _gen_alliance(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate alliance proposal action"""
        target = intention.target_country or "USSR"
        zone_id = intention.target_zone

        # Check current relations
        diplo = state.player.get_diplomacy_with(target)
        success_rate = 0.5 + (diplo.trust / 200) + (diplo.respect / 200)

        # Dynamic cost and risk
        cost = self._calculate_dynamic_cost(intention.type, state, zone_id)
        risk = self._calculate_dynamic_risk(intention.type, state, zone_id)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            zone_id=zone_id,
            name_fr="Proposition d'alliance",
            description_fr=f"Proposer un renforcement des liens avec {target}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=False,
            base_success_rate=success_rate,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="trust",
                    delta=15,
                    conditional=True,
                    description_fr="Confiance accrue si accepte",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="respect",
                    delta=5,
                    conditional=False,
                    description_fr="Respect accru par la demarche",
                ),
            ],
            predicted_effects={
                "trust": f"+15 si accepte (chance: {int(success_rate * 100)}%)",
                "respect": "+5",
            },
            resolution_type="negotiation",
            possible_outcomes=["accepted", "rejected", "counter_offer"],
        )

    def _gen_threat(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate threat action"""
        target = intention.target_country or "USSR"
        zone_id = intention.target_zone

        # Dynamic cost and risk
        cost = self._calculate_dynamic_cost(intention.type, state, zone_id)
        risk = self._calculate_dynamic_risk(intention.type, state, zone_id)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            zone_id=zone_id,
            name_fr="Avertissement",
            description_fr=f"Avertir {target} de consequences severes",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="fear",
                    delta=15,
                    description_fr="Peur accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="trust",
                    delta=-10,
                    description_fr="Confiance reduite",
                ),
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=5,
                    description_fr="Tension mondiale accrue",
                ),
            ],
            predicted_effects={
                "fear": "+15",
                "trust": "-10",
                "world_tension": "+5",
            },
            resolution_type="dice",
            possible_outcomes=["clean", "costly", "escalation"],
        )

    def _gen_negotiate(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate negotiation action"""
        target = intention.target_country or "USSR"
        topic = intention.topic or "desarmement"

        diplo = state.player.get_diplomacy_with(target)
        modifier = diplo.get_negotiation_modifier()

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            topic=topic,
            name_fr="Negociation",
            description_fr=f"Ouvrir des negociations avec {target} sur {topic}",
            political_cost=5,
            risk_level="low",
            success_guaranteed=False,
            base_success_rate=0.6 * modifier,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=-5,
                    conditional=True,
                    description_fr="Baisse des tensions si accord",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="trust",
                    delta=10,
                    conditional=True,
                    description_fr="Confiance accrue si accord",
                ),
            ],
            predicted_effects={
                "world_tension": "-5 si accord",
                "trust": "+10 si accord",
                "negotiation_modifier": f"{int(modifier * 100)}%",
            },
            resolution_type="negotiation",
            possible_outcomes=["agreement", "partial", "failed", "counter"],
        )

    def _gen_concede(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate concession action"""
        topic = intention.topic or "demande adverse"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            topic=topic,
            name_fr="Concession",
            description_fr=f"Accepter de ceder sur {topic}",
            political_cost=20,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=-10,
                    description_fr="Reduction significative des tensions",
                ),
                ActionEffect(
                    effect_type=EffectType.POLITICAL_CAPITAL,
                    target="player",
                    variable="political_capital",
                    delta=-10,
                    description_fr="Cout politique domestique",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target="USSR",
                    variable="leverage",
                    delta=-15,
                    description_fr="Perte de levier",
                ),
            ],
            predicted_effects={
                "world_tension": "-10",
                "political_capital": "-10",
                "leverage_ussr": "-15",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "costly"],
        )

    def _gen_sanction(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate sanction action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Sanctions diplomatiques",
            description_fr=f"Imposer des sanctions contre {target}",
            political_cost=15,
            risk_level="medium",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="fear",
                    delta=10,
                    description_fr="Peur accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="trust",
                    delta=-15,
                    description_fr="Confiance degradee",
                ),
                ActionEffect(
                    effect_type=EffectType.ADVERSARY,
                    target="adversary",
                    variable="pressure_economy",
                    delta=5,
                    description_fr="Pression economique sur l'adversaire",
                ),
            ],
            predicted_effects={
                "fear": "+10",
                "trust": "-15",
                "adversary_pressure": "+5",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "retaliation"],
        )

    def _gen_summit(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate summit action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Sommet diplomatique",
            description_fr=f"Organiser un sommet avec {target}",
            political_cost=10,
            risk_level="low",
            success_guaranteed=False,
            base_success_rate=0.7,
            effects=[
                ActionEffect(
                    effect_type=EffectType.REPUTATION,
                    target="player",
                    variable="international_reputation",
                    delta=10,
                    description_fr="Reputation internationale amelioree",
                ),
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=-10,
                    conditional=True,
                    description_fr="Tensions reduites si succes",
                ),
            ],
            predicted_effects={
                "reputation": "+10",
                "world_tension": "-10 si succes",
            },
            resolution_type="negotiation",
            possible_outcomes=["success", "partial", "failure", "incident"],
        )

    def _gen_backchannel(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate backchannel action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Canal secret",
            description_fr=f"Etablir un contact secret avec {target}",
            political_cost=5,
            risk_level="medium",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="trust",
                    delta=10,
                    description_fr="Confiance amelioree",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=10,
                    description_fr="Risque d'exposition accru",
                ),
            ],
            predicted_effects={
                "trust": "+10",
                "intel_exposure": "+10 (risque)",
            },
            resolution_type="dice",
            possible_outcomes=["secret_kept", "leak", "detected"],
        )

    # =========================================================================
    # MILITARY GENERATORS
    # =========================================================================

    def _gen_reinforce(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate military reinforcement action"""
        zone = intention.target_zone or "europe_west"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        # Dynamic cost and risk - reinforcing in hostile territory costs MORE
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Renforcement militaire",
            description_fr=f"Deployer des forces supplementaires en {zone_name}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.CONTROL,
                    target=zone,
                    variable="control_us",
                    delta=15,
                    description_fr="Controle renforce",
                ),
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_us",
                    delta=5,
                    description_fr="Influence accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=10,
                    description_fr="Tensions accrues",
                ),
            ],
            predicted_effects={
                "control_us": "+15",
                "influence_us": "+5",
                "world_tension": "+10",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "escalation"],
        )

    def _gen_withdraw(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate military withdrawal action"""
        zone = intention.target_zone or "europe_east"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        # Dynamic cost - withdrawal is usually cheap but can be politically risky
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Retrait militaire",
            description_fr=f"Reduire la presence militaire en {zone_name}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.CONTROL,
                    target=zone,
                    variable="control_us",
                    delta=-15,
                    description_fr="Controle reduit",
                ),
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=-10,
                    description_fr="Tensions reduites",
                ),
            ],
            predicted_effects={
                "control_us": "-15",
                "world_tension": "-10",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "perception_weak"],
        )

    def _gen_demo(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate military demonstration action"""
        zone = intention.target_zone or "central_america"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        # Dynamic cost - demo near enemy borders is much riskier/costlier
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Demonstration de force",
            description_fr=f"Demonstration de puissance militaire en {zone_name}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target="USSR",
                    variable="fear",
                    delta=15,
                    description_fr="Peur accrue chez l'adversaire",
                ),
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_us",
                    delta=10,
                    description_fr="Influence locale accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=15,
                    description_fr="Forte hausse des tensions",
                ),
            ],
            predicted_effects={
                "fear_ussr": "+15",
                "influence_us": "+10",
                "world_tension": "+15",
            },
            resolution_type="dice",
            possible_outcomes=["intimidation", "incident", "escalation"],
        )

    def _gen_proxy(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate proxy war action"""
        zone = intention.target_zone or "southeast_asia"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        # Dynamic cost - proxy wars in strategic zones cost much more
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Soutien aux forces locales",
            description_fr=f"Armer et financer des forces alliees en {zone_name}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=False,
            base_success_rate=0.65,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_us",
                    delta=15,
                    conditional=True,
                    description_fr="Influence accrue si succes",
                ),
                ActionEffect(
                    effect_type=EffectType.STABILITY,
                    target=zone,
                    variable="stability",
                    delta=-20,
                    description_fr="Destabilisation de la zone",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=15,
                    description_fr="Risque d'exposition",
                ),
            ],
            predicted_effects={
                "influence_us": "+15 si succes",
                "stability": "-20",
                "intel_exposure": "+15",
            },
            resolution_type="dice",
            possible_outcomes=["success", "partial", "failure", "exposed"],
        )

    def _gen_blockade(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate blockade action"""
        target = intention.target_country or "USSR"
        zone = intention.target_zone or "central_america"

        # Dynamic cost - blockades are VERY expensive and risky, especially at low DEFCON
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            country_id=target,
            name_fr="Blocus naval",
            description_fr=f"Etablir un blocus naval contre {target}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="defcon",
                    delta=-1,
                    description_fr="DEFCON baisse d'un niveau",
                ),
                ActionEffect(
                    effect_type=EffectType.DEFCON,
                    target="global",
                    variable="world_tension",
                    delta=25,
                    description_fr="Tensions au maximum",
                ),
                ActionEffect(
                    effect_type=EffectType.ADVERSARY,
                    target="adversary",
                    variable="pressure_economy",
                    delta=15,
                    description_fr="Forte pression economique",
                ),
            ],
            predicted_effects={
                "defcon": "-1 niveau",
                "world_tension": "+25",
                "adversary_pressure": "+15",
            },
            resolution_type="dice",
            possible_outcomes=["success", "confrontation", "war"],
            warnings=["Action tres risquee - risque d'escalade nucleaire"],
        )

    def _gen_base(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate military base action"""
        zone = intention.target_zone or "turkey_greece"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        # Dynamic cost - bases in contested/strategic zones cost much more
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Construction de base",
            description_fr=f"Etablir une nouvelle base militaire en {zone_name}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.CONTROL,
                    target=zone,
                    variable="control_us",
                    delta=20,
                    description_fr="Controle significativement renforce",
                ),
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_us",
                    delta=10,
                    description_fr="Influence accrue",
                ),
            ],
            predicted_effects={
                "control_us": "+20",
                "influence_us": "+10",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "local_opposition"],
        )

    # =========================================================================
    # COVERT GENERATORS
    # =========================================================================

    def _gen_destab(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate destabilization action"""
        zone = intention.target_zone or "europe_east"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        # Dynamic cost - destabilizing stable enemy territory is EXPENSIVE
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Operation de destabilisation",
            description_fr=f"Soutenir l'opposition en {zone_name}",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=False,
            base_success_rate=0.55,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_ussr",
                    delta=-15,
                    conditional=True,
                    description_fr="Affaiblissement influence adverse",
                ),
                ActionEffect(
                    effect_type=EffectType.STABILITY,
                    target=zone,
                    variable="stability",
                    delta=-15,
                    description_fr="Destabilisation",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=20,
                    description_fr="Risque d'exposition eleve",
                ),
            ],
            predicted_effects={
                "influence_ussr": "-15 si succes",
                "stability": "-15",
                "intel_exposure": "+20",
            },
            resolution_type="dice",
            possible_outcomes=["success", "partial", "exposed", "blowback"],
        )

    def _gen_coup(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate coup action - THE BIG ONE

        A coup in Belgium vs China should have WILDLY different costs.
        This is where dynamic costs matter most!
        """
        target = intention.target_country
        zone = intention.target_zone

        # Dynamic cost - coup in a major power's sphere is INSANELY expensive
        cost = self._calculate_dynamic_cost(intention.type, state, zone)
        risk = self._calculate_dynamic_risk(intention.type, state, zone)

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            country_id=target,
            name_fr="Coup d'etat",
            description_fr=f"Organiser un changement de regime",
            political_cost=cost,
            risk_level=risk,
            success_guaranteed=False,
            base_success_rate=0.40,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone or "target",
                    variable="influence_us",
                    delta=40,
                    conditional=True,
                    description_fr="Gain massif d'influence si succes",
                ),
                ActionEffect(
                    effect_type=EffectType.STABILITY,
                    target=zone or "target",
                    variable="stability",
                    delta=-30,
                    description_fr="Instabilite majeure",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=35,
                    description_fr="Exposition quasi-certaine",
                ),
                ActionEffect(
                    effect_type=EffectType.REPUTATION,
                    target="player",
                    variable="international_reputation",
                    delta=-20,
                    conditional=True,
                    description_fr="Reputation ternie si expose",
                ),
            ],
            predicted_effects={
                "influence_us": "+40 si succes",
                "stability": "-30",
                "intel_exposure": "+35",
                "reputation": "-20 si expose",
            },
            resolution_type="dice",
            possible_outcomes=["success", "failure", "exposed", "civil_war"],
            warnings=["Operation tres risquee", "Consequences graves si exposee"],
        )

    def _gen_sabotage(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate sabotage action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Sabotage",
            description_fr=f"Saboter les installations de {target}",
            political_cost=25,
            risk_level="high",
            success_guaranteed=False,
            base_success_rate=0.50,
            effects=[
                ActionEffect(
                    effect_type=EffectType.ADVERSARY,
                    target="adversary",
                    variable="pressure_economy",
                    delta=10,
                    conditional=True,
                    description_fr="Pression economique si succes",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=25,
                    description_fr="Risque d'exposition",
                ),
            ],
            predicted_effects={
                "adversary_pressure": "+10 si succes",
                "intel_exposure": "+25",
            },
            resolution_type="dice",
            possible_outcomes=["success", "partial", "failed", "detected"],
        )

    def _gen_assassin(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate assassination action"""
        target = intention.target_country

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Elimination",
            description_fr="Neutraliser un leader ennemi",
            political_cost=40,
            risk_level="extreme",
            success_guaranteed=False,
            base_success_rate=0.30,
            effects=[
                ActionEffect(
                    effect_type=EffectType.STABILITY,
                    target=target or "target",
                    variable="stability",
                    delta=-40,
                    conditional=True,
                    description_fr="Destabilisation majeure si succes",
                ),
                ActionEffect(
                    effect_type=EffectType.REPUTATION,
                    target="player",
                    variable="international_reputation",
                    delta=-30,
                    description_fr="Reputation gravement atteinte si expose",
                ),
            ],
            predicted_effects={
                "target_stability": "-40 si succes",
                "reputation": "-30 si expose",
            },
            resolution_type="dice",
            possible_outcomes=["success", "failed", "martyr", "war"],
            warnings=["Action immorale", "Consequences catastrophiques si expose"],
        )

    def _gen_propaganda(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate propaganda action"""
        zone = intention.target_zone or "europe_east"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Campagne de propagande",
            description_fr=f"Lancer une campagne de propagande en {zone_name}",
            political_cost=10,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_us",
                    delta=5,
                    description_fr="Influence legèrement accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_ussr",
                    delta=-5,
                    description_fr="Influence adverse reduite",
                ),
            ],
            predicted_effects={
                "influence_us": "+5",
                "influence_ussr": "-5",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "backfire"],
        )

    # =========================================================================
    # INTEL GENERATORS
    # =========================================================================

    def _gen_intel_collect(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate intel collection action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Collecte de renseignements",
            description_fr=f"Collecter des informations sur {target}",
            political_cost=10,
            risk_level="medium",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable=f"intel_{target}",
                    delta=15,
                    description_fr="Intel sur la cible amelioree",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=10,
                    description_fr="Risque d'exposition",
                ),
            ],
            predicted_effects={
                f"intel_{target}": "+15",
                "intel_exposure": "+10",
            },
            resolution_type="dice",
            possible_outcomes=["success", "partial", "disinformation", "detected"],
        )

    def _gen_intel_verify(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate intel verification action"""
        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            name_fr="Verification intel",
            description_fr="Verifier la fiabilite des renseignements",
            political_cost=5,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_reliability",
                    delta=10,
                    description_fr="Fiabilite intel amelioree",
                ),
            ],
            predicted_effects={
                "intel_reliability": "+10",
            },
            resolution_type="automatic",
            possible_outcomes=["confirmed", "unconfirmed", "disinformation_revealed"],
        )

    def _gen_intel_counter(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate counter-intelligence action"""
        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            name_fr="Contre-espionnage",
            description_fr="Renforcer les mesures de contre-espionnage",
            political_cost=15,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=-20,
                    description_fr="Exposition reduite",
                ),
            ],
            predicted_effects={
                "intel_exposure": "-20",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "mole_found"],
        )

    def _gen_intel_disinfo(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate disinformation action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Desinformation",
            description_fr=f"Diffuser de fausses informations a {target}",
            political_cost=15,
            risk_level="medium",
            success_guaranteed=False,
            base_success_rate=0.60,
            effects=[
                ActionEffect(
                    effect_type=EffectType.ADVERSARY,
                    target="adversary",
                    variable="intel_quality",
                    delta=-15,
                    conditional=True,
                    description_fr="Intel adverse degradee",
                ),
            ],
            predicted_effects={
                "adversary_intel": "-15 si succes",
            },
            resolution_type="dice",
            possible_outcomes=["believed", "ignored", "exposed"],
        )

    # =========================================================================
    # ECONOMIC GENERATORS
    # =========================================================================

    def _gen_eco_aid(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate economic aid action"""
        target = intention.target_country
        zone = intention.target_zone

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            country_id=target,
            name_fr="Aide economique",
            description_fr=f"Envoyer de l'aide economique",
            political_cost=15,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone or target or "target",
                    variable="influence_us",
                    delta=10,
                    description_fr="Influence accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target or "allies",
                    variable="leverage",
                    delta=10,
                    description_fr="Levier diplomatique accru",
                ),
            ],
            predicted_effects={
                "influence_us": "+10",
                "leverage": "+10",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "misappropriated"],
        )

    def _gen_eco_trade(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate trade agreement action"""
        target = intention.target_country

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Accord commercial",
            description_fr=f"Etablir un accord commercial",
            political_cost=10,
            risk_level="low",
            success_guaranteed=False,
            base_success_rate=0.75,
            effects=[
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target or "partner",
                    variable="trust",
                    delta=10,
                    conditional=True,
                    description_fr="Confiance accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target or "partner",
                    variable="leverage",
                    delta=5,
                    conditional=True,
                    description_fr="Levier accru",
                ),
            ],
            predicted_effects={
                "trust": "+10 si accepte",
                "leverage": "+5 si accepte",
            },
            resolution_type="negotiation",
            possible_outcomes=["accepted", "rejected", "counter"],
        )

    def _gen_eco_embargo(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate embargo action"""
        target = intention.target_country or "USSR"

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            country_id=target,
            name_fr="Embargo economique",
            description_fr=f"Imposer un embargo contre {target}",
            political_cost=20,
            risk_level="medium",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.ADVERSARY,
                    target="adversary",
                    variable="pressure_economy",
                    delta=15,
                    description_fr="Pression economique forte",
                ),
                ActionEffect(
                    effect_type=EffectType.DIPLOMACY,
                    target=target,
                    variable="trust",
                    delta=-20,
                    description_fr="Relations degradees",
                ),
            ],
            predicted_effects={
                "adversary_pressure": "+15",
                "trust": "-20",
            },
            resolution_type="automatic",
            possible_outcomes=["effective", "circumvented", "retaliation"],
        )

    def _gen_eco_invest(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate investment action"""
        zone = intention.target_zone or "south_america"
        zone_obj = state.zones.get(zone)
        zone_name = zone_obj.name_fr if zone_obj else zone

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Investissement",
            description_fr=f"Investir dans le developpement en {zone_name}",
            political_cost=20,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone,
                    variable="influence_us",
                    delta=10,
                    description_fr="Influence accrue",
                ),
                ActionEffect(
                    effect_type=EffectType.STABILITY,
                    target=zone,
                    variable="stability",
                    delta=10,
                    description_fr="Stabilite amelioree",
                ),
            ],
            predicted_effects={
                "influence_us": "+10",
                "stability": "+10",
            },
            resolution_type="automatic",
            possible_outcomes=["clean", "nationalized"],
        )

    # =========================================================================
    # DOMESTIC GENERATORS
    # =========================================================================

    def _gen_dom_speech(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate public speech action"""
        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            name_fr="Discours public",
            description_fr="Faire une declaration publique",
            political_cost=5,
            risk_level="low",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.POLITICAL_CAPITAL,
                    target="player",
                    variable="domestic_stability",
                    delta=5,
                    description_fr="Soutien interieur renforce",
                ),
                ActionEffect(
                    effect_type=EffectType.REPUTATION,
                    target="player",
                    variable="international_reputation",
                    delta=5,
                    description_fr="Image internationale amelioree",
                ),
            ],
            predicted_effects={
                "domestic_stability": "+5",
                "reputation": "+5",
            },
            resolution_type="automatic",
            possible_outcomes=["well_received", "controversial"],
        )

    def _gen_dom_reform(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate reform action"""
        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            name_fr="Reforme interieure",
            description_fr="Lancer des reformes politiques",
            political_cost=25,
            risk_level="medium",
            success_guaranteed=False,
            base_success_rate=0.70,
            effects=[
                ActionEffect(
                    effect_type=EffectType.POLITICAL_CAPITAL,
                    target="player",
                    variable="domestic_stability",
                    delta=15,
                    conditional=True,
                    description_fr="Stabilite amelioree si succes",
                ),
                ActionEffect(
                    effect_type=EffectType.POLITICAL_CAPITAL,
                    target="player",
                    variable="political_capital",
                    delta=10,
                    conditional=True,
                    description_fr="Capital accru si succes",
                ),
            ],
            predicted_effects={
                "domestic_stability": "+15 si succes",
                "political_capital": "+10 si succes",
            },
            resolution_type="dice",
            possible_outcomes=["success", "partial", "opposition", "failure"],
        )

    def _gen_dom_repress(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate repression action"""
        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            name_fr="Repression",
            description_fr="Reprimer l'opposition interieure",
            political_cost=15,
            risk_level="medium",
            success_guaranteed=True,
            effects=[
                ActionEffect(
                    effect_type=EffectType.POLITICAL_CAPITAL,
                    target="player",
                    variable="domestic_stability",
                    delta=10,
                    description_fr="Stabilite a court terme",
                ),
                ActionEffect(
                    effect_type=EffectType.REPUTATION,
                    target="player",
                    variable="international_reputation",
                    delta=-10,
                    description_fr="Reputation ternie",
                ),
            ],
            predicted_effects={
                "domestic_stability": "+10",
                "reputation": "-10",
            },
            resolution_type="automatic",
            possible_outcomes=["effective", "backlash", "international_condemnation"],
        )

    def _gen_dom_election(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Generate election action"""
        zone = intention.target_zone

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=zone,
            name_fr="Influence electorale",
            description_fr="Influencer les elections",
            political_cost=20,
            risk_level="medium",
            success_guaranteed=False,
            base_success_rate=0.55,
            effects=[
                ActionEffect(
                    effect_type=EffectType.INFLUENCE,
                    target=zone or "target",
                    variable="influence_us",
                    delta=20,
                    conditional=True,
                    description_fr="Influence accrue si succes",
                ),
                ActionEffect(
                    effect_type=EffectType.INTEL,
                    target="player",
                    variable="intel_exposure",
                    delta=15,
                    description_fr="Risque d'exposition",
                ),
            ],
            predicted_effects={
                "influence_us": "+20 si succes",
                "intel_exposure": "+15",
            },
            resolution_type="dice",
            possible_outcomes=["success", "partial", "exposed", "backfire"],
        )

    # =========================================================================
    # DEFAULT GENERATOR
    # =========================================================================

    def _gen_default(self, intention: ParsedIntention, state: NarrativeWorldState) -> GeneratedAction:
        """Default generator for unhandled intentions"""
        meta = INTENTION_METADATA.get(intention.type, {})

        return GeneratedAction(
            id=self._next_id(),
            intention_id=intention.id,
            intention_type=intention.type,
            zone_id=intention.target_zone,
            country_id=intention.target_country,
            name_fr=meta.get("name_fr", "Action"),
            description_fr=intention.description_fr or "Action en cours",
            political_cost=meta.get("political_cost", 10),
            risk_level=meta.get("risk_base", "medium"),
            success_guaranteed=True,
            effects=[],
            predicted_effects={},
            resolution_type="automatic",
            possible_outcomes=["success", "partial"],
        )

    # =========================================================================
    # WARNINGS CHECKER
    # =========================================================================

    def _check_warnings(self, action: GeneratedAction, state: NarrativeWorldState) -> List[str]:
        """Check for warnings based on state"""
        warnings = []

        # Low political capital
        if state.player.political_capital < action.political_cost + 10:
            warnings.append("Capital politique limite apres cette action")

        # High DEFCON with risky action
        if state.defcon <= 3 and action.risk_level in ["high", "extreme"]:
            warnings.append("Attention: tensions elevees, risque d'escalade nucleaire")

        # High intel exposure
        if state.player.intel_exposure > 70:
            warnings.append("Exposition intel critique - risque de detection eleve")

        # Zone stability
        if action.zone_id:
            zone = state.zones.get(action.zone_id)
            if zone and zone.stability < 30:
                warnings.append(f"Zone instable - effets impredictibles")

        return warnings
