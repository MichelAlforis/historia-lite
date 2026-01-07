"""AI Perception Engine - Fog of War for Adversary AI

L'IA ne joue pas contre le backend.
Elle joue contre sa propre carte du monde.

Architecture:
    REALITE (NarrativeWorldState)
        ↓
    build_observations() → Observations (PUBLIC + COVERT)
        ↓
    update_beliefs() → AIBeliefs (croyances qualitatives)
        ↓
    get_faction_proposals() → FactionProposal[]
        ↓
    leader_arbitrates() → Action choisie

L'IA raisonne en TAGS qualitatifs, pas en chiffres.
"""
import logging
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ConfidenceBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResolveLevel(str, Enum):
    WEAK = "weak"
    HESITANT = "hesitant"
    DETERMINED = "determined"
    IRON = "iron"


class OpportunityLevel(str, Enum):
    NONE = "none"
    POSSIBLE = "possible"
    RIPE = "ripe"


class ThreatLevel(str, Enum):
    NONE = "none"
    WATCH = "watch"
    URGENT = "urgent"


class NuclearRisk(str, Enum):
    MANAGEABLE = "manageable"
    ELEVATED = "elevated"
    CRITICAL = "critical"


class IntelReliability(str, Enum):
    CONFIRMED = "confirmed"      # 90-100%
    PROBABLE = "probable"        # 70-90%
    RUMOR = "rumor"             # 40-70%
    DISINFORMATION = "disinformation"  # faux


# =============================================================================
# OBSERVATIONS (ce que l'IA peut "voir")
# =============================================================================

@dataclass
class Observation:
    """Un fait observable par l'IA"""
    source: str                  # "satellite", "kgb", "press", "diplomacy"
    zone: Optional[str]          # zone concernee
    fact_type: str               # "troop_movement", "political_speech", etc.
    content: str                 # description narrative
    reliability: IntelReliability
    age_turns: int = 0           # 0 = ce tour, +1 = tour precedent


@dataclass
class WorldObservations:
    """Tout ce que l'IA observe (PAS la realite)"""
    public_intel: List[Observation] = field(default_factory=list)
    covert_intel: List[Observation] = field(default_factory=list)
    last_player_actions: List[str] = field(default_factory=list)
    silence_streak: int = 0      # tours sans action joueur


# =============================================================================
# BELIEFS (croyances qualitatives)
# =============================================================================

@dataclass
class ZoneBelief:
    """Croyance sur une zone (pas les vrais chiffres)"""
    zone_id: str
    control_band: str                    # "US", "USSR", "CONTESTED"
    stability_band: ConfidenceBand
    opportunity_level: OpportunityLevel
    threat_level: ThreatLevel
    confidence: ConfidenceBand
    tags: List[str] = field(default_factory=list)


@dataclass
class PlayerBelief:
    """Croyance sur le joueur (Kennedy/USA)"""
    resolve: ResolveLevel
    domestic_support: ConfidenceBand
    military_readiness: ConfidenceBand
    likely_strategy: str                 # "aggressive", "cautious", "unpredictable"
    tags: List[str] = field(default_factory=list)


@dataclass
class AIBeliefs:
    """Toutes les croyances de l'IA"""
    player: PlayerBelief
    zones: Dict[str, ZoneBelief] = field(default_factory=dict)
    global_tension: ConfidenceBand = ConfidenceBand.MEDIUM
    nuclear_risk: NuclearRisk = NuclearRisk.MANAGEABLE
    opportunity_window: bool = False
    turn: int = 0


# =============================================================================
# FACTION PROPOSALS
# =============================================================================

@dataclass
class FactionProposal:
    """Proposition d'une faction (KGB, Armee, Politburo)"""
    faction: str                # "kgb", "army", "politburo"
    action_type: str            # type d'action proposee
    target_zone: Optional[str]  # zone cible
    target_country: Optional[str]
    intensity: str              # "light", "moderate", "heavy"
    rationale: str              # justification narrative
    rationale_fr: str           # en francais


# =============================================================================
# AI ERRORS (pour tracking et debrief)
# =============================================================================

@dataclass
class AIError:
    """Une erreur de l'IA (pour le debrief)"""
    turn: int
    error_type: str             # "overestimation", "underestimation", "misread"
    subject: str                # "player_resolve", "zone_stability", etc.
    belief: str                 # ce que l'IA croyait
    reality: str                # ce qui etait vrai
    consequence: str            # ce qui s'est passe
    consequence_fr: str
    # Donnees factuelles pour ancrage narratif
    zone: Optional[str] = None          # zone concernee
    action_taken: Optional[str] = None  # action prise suite a l'erreur
    result: Optional[str] = None        # resultat de l'action
    escalation_delta: int = 0           # impact sur la tension
    factions: Optional[List[str]] = None  # factions impliquees (pour faction_conflict)


# =============================================================================
# INTEL QUALITY TABLE
# =============================================================================

INTEL_QUALITY = {
    # Type d'intel → fiabilite de base (0-100)
    "public_speech": 95,
    "press_report": 90,
    "troop_movement_visible": 80,
    "diplomatic_channel": 75,
    "satellite_imagery": 70,
    "covert_source": 50,
    "intercept": 45,
    "rumor": 30,
    "defector_report": 40,
    "domestic_us_politics": 25,  # tres difficile a lire
}


# =============================================================================
# BELIEF TAGS
# =============================================================================

BELIEF_TAGS = {
    # Sur les zones
    "protests_exaggerated": "surestimation de l'instabilite",
    "ally_unreliable": "doute sur la fiabilite des allies US",
    "missiles_operational_soon": "urgence sur les missiles",
    "resistance_underestimated": "zone plus solide que prevu",
    "economic_weakness": "faiblesse economique percue",
    "military_buildup": "renforcement militaire detecte",

    # Sur le joueur
    "bluffing": "croit que le joueur bluffe",
    "paralyzed_by_congress": "croit le joueur bloque politiquement",
    "preparing_strike": "croit a une attaque imminente",
    "willing_to_negotiate": "croit le joueur ouvert a la negoce",
    "domestic_crisis": "croit a une crise interne US",
    "military_weak": "sous-estime la puissance militaire",
}


# =============================================================================
# PERCEPTION ENGINE
# =============================================================================

class AIPerceptionEngine:
    """Genere la vision deformee du monde pour l'IA"""

    def __init__(self):
        self.errors: List[AIError] = []
        self.beliefs_history: List[AIBeliefs] = []

    def build_observations(
        self,
        real_state: Any,  # NarrativeWorldState
        last_player_actions: List[Dict[str, Any]],
    ) -> WorldObservations:
        """Transforme la realite en observations (avec pertes d'info)"""
        observations = WorldObservations()

        # Actions joueur visibles
        for action in last_player_actions:
            action_type = action.get("type", "unknown")
            # Seules les actions publiques sont visibles
            if self._is_visible_action(action_type):
                observations.last_player_actions.append(action_type)

        # Silence streak
        observations.silence_streak = getattr(real_state, "silence_streak", 0)

        # Intel PUBLIC (haute fiabilite)
        observations.public_intel.extend(
            self._build_public_intel(real_state)
        )

        # Intel COVERT (fiabilite variable, peut etre faux)
        observations.covert_intel.extend(
            self._build_covert_intel(real_state)
        )

        return observations

    def _is_visible_action(self, action_type: str) -> bool:
        """Determine si une action joueur est visible"""
        visible_actions = {
            "blockade", "negotiate", "public_speech", "military_demo",
            "reinforce", "alliance", "un_resolution", "summit",
        }
        return any(v in action_type.lower() for v in visible_actions)

    def _build_public_intel(self, state: Any) -> List[Observation]:
        """Construit l'intel public (quasi-fiable)"""
        intel = []

        # DEFCON est public
        intel.append(Observation(
            source="press",
            zone=None,
            fact_type="defcon_level",
            content=f"DEFCON niveau {state.defcon}",
            reliability=IntelReliability.CONFIRMED,
        ))

        # Tensions mondiales (approximatif)
        tension_band = "haute" if state.world_tension > 60 else (
            "moderee" if state.world_tension > 30 else "basse"
        )
        intel.append(Observation(
            source="press",
            zone=None,
            fact_type="global_tension",
            content=f"Tension mondiale {tension_band}",
            reliability=IntelReliability.CONFIRMED,
        ))

        # Zones avec crises publiques
        for zone_id, zone in state.zones.items():
            if zone.has_crisis:
                intel.append(Observation(
                    source="press",
                    zone=zone_id,
                    fact_type="crisis",
                    content=f"Crise en cours dans {zone_id}",
                    reliability=IntelReliability.CONFIRMED,
                ))

        return intel

    def _build_covert_intel(self, state: Any) -> List[Observation]:
        """Construit l'intel covert (peut etre faux)"""
        intel = []

        # Stabilite joueur (tres difficile a lire)
        player_stability = state.player.domestic_stability
        # Ajouter du bruit
        perceived = self._add_perception_noise(player_stability, noise=20)

        if perceived < 40:
            content = "Sources indiquent instabilite politique a Washington"
        elif perceived < 60:
            content = "Situation politique US incertaine"
        else:
            content = "Administration semble stable"

        # Fiabilite variable
        reliability = random.choice([
            IntelReliability.PROBABLE,
            IntelReliability.RUMOR,
        ])

        intel.append(Observation(
            source="kgb",
            zone=None,
            fact_type="domestic_us_politics",
            content=content,
            reliability=reliability,
        ))

        # Intel sur les zones (variable)
        for zone_id, zone in state.zones.items():
            # 50% de chance d'avoir de l'intel sur chaque zone
            if random.random() < 0.5:
                # Bruit sur la stabilite
                perceived_stability = self._add_perception_noise(
                    zone.stability, noise=15
                )

                if perceived_stability < 40:
                    content = f"Zone {zone_id} semble fragile"
                elif perceived_stability < 60:
                    content = f"Situation incertaine en {zone_id}"
                else:
                    content = f"Zone {zone_id} parait stable"

                intel.append(Observation(
                    source="kgb",
                    zone=zone_id,
                    fact_type="zone_stability",
                    content=content,
                    reliability=random.choice([
                        IntelReliability.PROBABLE,
                        IntelReliability.RUMOR,
                    ]),
                ))

        return intel

    def _add_perception_noise(self, value: int, noise: int) -> int:
        """Ajoute du bruit a une valeur (sans gauss pour eviter le 'simulateur')"""
        # Variation discrete plutot que continue
        variations = [-noise, -noise//2, 0, noise//2, noise]
        delta = random.choice(variations)
        return max(0, min(100, value + delta))

    def update_beliefs(
        self,
        observations: WorldObservations,
        adversary: Any,  # AdversaryState
        previous_beliefs: Optional[AIBeliefs] = None,
    ) -> AIBeliefs:
        """Met a jour les croyances basees sur les observations"""
        beliefs = AIBeliefs(
            player=self._infer_player_belief(observations, adversary),
            turn=getattr(adversary, "turn", 0),
        )

        # Tension globale
        beliefs.global_tension = self._infer_global_tension(observations)

        # Risque nucleaire
        beliefs.nuclear_risk = self._infer_nuclear_risk(observations, adversary)

        # Fenetre d'opportunite
        beliefs.opportunity_window = self._infer_opportunity_window(
            observations, adversary
        )

        # Croyances sur les zones
        beliefs.zones = self._infer_zone_beliefs(observations, adversary)

        # Stocker dans l'historique
        self.beliefs_history.append(beliefs)

        return beliefs

    def _infer_player_belief(
        self,
        observations: WorldObservations,
        adversary: Any,
    ) -> PlayerBelief:
        """Infere les croyances sur le joueur"""
        # Analyser le silence
        if observations.silence_streak >= 3:
            resolve = ResolveLevel.WEAK
            tags = ["paralyzed_by_congress"]
        elif observations.silence_streak >= 2:
            resolve = ResolveLevel.HESITANT
            tags = []
        elif "blockade" in " ".join(observations.last_player_actions):
            resolve = ResolveLevel.DETERMINED
            tags = ["preparing_strike"] if adversary.risk_tolerance > 60 else []
        elif "negotiate" in " ".join(observations.last_player_actions):
            resolve = ResolveLevel.HESITANT
            tags = ["willing_to_negotiate"]
        else:
            resolve = ResolveLevel.DETERMINED
            tags = []

        # Biais de personnalite
        if adversary.impulsivity > 60:
            # Impulsif : tendance a sous-estimer l'adversaire
            if resolve == ResolveLevel.DETERMINED:
                resolve = ResolveLevel.HESITANT
                tags.append("bluffing")

        # Inferer le support domestique (difficile)
        domestic_support = ConfidenceBand.MEDIUM
        for obs in observations.covert_intel:
            if "instabilite" in obs.content.lower():
                domestic_support = ConfidenceBand.LOW
                tags.append("domestic_crisis")
                break

        # Strategie probable
        if "blockade" in " ".join(observations.last_player_actions):
            likely_strategy = "aggressive"
        elif "negotiate" in " ".join(observations.last_player_actions):
            likely_strategy = "cautious"
        else:
            likely_strategy = "unpredictable"

        return PlayerBelief(
            resolve=resolve,
            domestic_support=domestic_support,
            military_readiness=ConfidenceBand.HIGH,  # toujours presume
            likely_strategy=likely_strategy,
            tags=tags,
        )

    def _infer_global_tension(
        self,
        observations: WorldObservations,
    ) -> ConfidenceBand:
        """Infere le niveau de tension globale"""
        for obs in observations.public_intel:
            if obs.fact_type == "global_tension":
                if "haute" in obs.content:
                    return ConfidenceBand.HIGH
                elif "basse" in obs.content:
                    return ConfidenceBand.LOW
        return ConfidenceBand.MEDIUM

    def _infer_nuclear_risk(
        self,
        observations: WorldObservations,
        adversary: Any,
    ) -> NuclearRisk:
        """Infere le risque nucleaire percu"""
        defcon = 5  # default
        for obs in observations.public_intel:
            if obs.fact_type == "defcon_level":
                try:
                    defcon = int(obs.content.split()[-1])
                except (ValueError, IndexError):
                    pass

        if defcon <= 2:
            return NuclearRisk.CRITICAL
        elif defcon <= 3:
            return NuclearRisk.ELEVATED
        else:
            # Biais : risk-tolerant minimise le danger
            if adversary.risk_tolerance > 70:
                return NuclearRisk.MANAGEABLE
            return NuclearRisk.ELEVATED if defcon == 4 else NuclearRisk.MANAGEABLE

    def _infer_opportunity_window(
        self,
        observations: WorldObservations,
        adversary: Any,
    ) -> bool:
        """Determine si l'IA croit que c'est le moment d'agir"""
        # Silence du joueur = opportunite
        if observations.silence_streak >= 2:
            return True

        # Doctrine expansion + zones contestees
        from .narrative_state import AdversaryDoctrine
        if adversary.doctrine == AdversaryDoctrine.EXPANSION:
            # Biais : voit des opportunites partout
            if adversary.impulsivity > 50:
                return True

        return False

    def _infer_zone_beliefs(
        self,
        observations: WorldObservations,
        adversary: Any,
    ) -> Dict[str, ZoneBelief]:
        """Infere les croyances sur chaque zone"""
        zone_beliefs = {}

        # Collecter l'intel par zone
        zone_intel: Dict[str, List[Observation]] = {}
        for obs in observations.public_intel + observations.covert_intel:
            if obs.zone:
                zone_intel.setdefault(obs.zone, []).append(obs)

        # Zones prioritaires de l'adversaire
        priority_zones = getattr(adversary, "priority_zones", [])

        for zone_id, intel_list in zone_intel.items():
            # Analyser l'intel
            has_crisis = any("crise" in o.content.lower() for o in intel_list)
            seems_fragile = any("fragile" in o.content.lower() for o in intel_list)
            seems_stable = any("stable" in o.content.lower() for o in intel_list)

            # Determiner les bandes
            if seems_fragile:
                stability_band = ConfidenceBand.LOW
            elif seems_stable:
                stability_band = ConfidenceBand.HIGH
            else:
                stability_band = ConfidenceBand.MEDIUM

            # Opportunite
            opportunity = OpportunityLevel.NONE
            if has_crisis or seems_fragile:
                opportunity = OpportunityLevel.POSSIBLE
                if zone_id in priority_zones:
                    opportunity = OpportunityLevel.RIPE

            # Menace
            threat = ThreatLevel.NONE
            if has_crisis:
                threat = ThreatLevel.WATCH

            # Tags
            tags = []
            if seems_fragile and not has_crisis:
                # Peut-etre fausse impression
                if random.random() < 0.3:
                    tags.append("protests_exaggerated")

            # Confiance
            high_reliability = sum(
                1 for o in intel_list
                if o.reliability in [IntelReliability.CONFIRMED, IntelReliability.PROBABLE]
            )
            if high_reliability > len(intel_list) / 2:
                confidence = ConfidenceBand.HIGH
            elif high_reliability > 0:
                confidence = ConfidenceBand.MEDIUM
            else:
                confidence = ConfidenceBand.LOW

            zone_beliefs[zone_id] = ZoneBelief(
                zone_id=zone_id,
                control_band="CONTESTED",  # par defaut, affine plus tard
                stability_band=stability_band,
                opportunity_level=opportunity,
                threat_level=threat,
                confidence=confidence,
                tags=tags,
            )

        return zone_beliefs

    def get_faction_proposals(
        self,
        beliefs: AIBeliefs,
        adversary: Any,
    ) -> List[FactionProposal]:
        """Chaque faction propose son plan"""
        proposals = []

        # === KGB : prefere covert, destab ===
        for zone_id, zone_belief in beliefs.zones.items():
            if zone_belief.stability_band == ConfidenceBand.LOW:
                proposals.append(FactionProposal(
                    faction="kgb",
                    action_type="destabilize",
                    target_zone=zone_id,
                    target_country=None,
                    intensity="moderate",
                    rationale=f"{zone_id} appears fragile. We should exploit this.",
                    rationale_fr=f"{zone_id} semble fragile. Profitons-en.",
                ))
                break  # Une seule proposition KGB

        # Fallback KGB
        if not any(p.faction == "kgb" for p in proposals):
            proposals.append(FactionProposal(
                faction="kgb",
                action_type="intel_op",
                target_zone=None,
                target_country="USA",
                intensity="light",
                rationale="Gather more intelligence on American intentions.",
                rationale_fr="Renforcer le renseignement sur les intentions americaines.",
            ))

        # === ARMEE : prefere force, demonstration ===
        if beliefs.player.resolve in [ResolveLevel.WEAK, ResolveLevel.HESITANT]:
            proposals.append(FactionProposal(
                faction="army",
                action_type="military_demo",
                target_zone=adversary.priority_zones[0] if adversary.priority_zones else "europe_east",
                target_country=None,
                intensity="heavy",
                rationale="The American President hesitates. Show our strength.",
                rationale_fr="Le President americain hesite. Montrons notre force.",
            ))
        else:
            proposals.append(FactionProposal(
                faction="army",
                action_type="arms_buildup",
                target_zone=None,
                target_country=None,
                intensity="moderate",
                rationale="Maintain military readiness.",
                rationale_fr="Maintenir la capacite militaire.",
            ))

        # === POLITBURO : prefere diplomatie, prudence ===
        if beliefs.nuclear_risk in [NuclearRisk.ELEVATED, NuclearRisk.CRITICAL]:
            proposals.append(FactionProposal(
                faction="politburo",
                action_type="propose_talks",
                target_zone=None,
                target_country="USA",
                intensity="light",
                rationale="The risk is too high. We must open a channel.",
                rationale_fr="Le risque est trop eleve. Ouvrons un canal.",
            ))
        elif "willing_to_negotiate" in beliefs.player.tags:
            proposals.append(FactionProposal(
                faction="politburo",
                action_type="propose_talks",
                target_zone=None,
                target_country="USA",
                intensity="moderate",
                rationale="They seem open to dialogue. Seize the opportunity.",
                rationale_fr="Ils semblent ouverts au dialogue. Saisissons l'opportunite.",
            ))
        else:
            proposals.append(FactionProposal(
                faction="politburo",
                action_type="consolidate",
                target_zone=None,
                target_country=None,
                intensity="light",
                rationale="Consolidate our internal position.",
                rationale_fr="Consolider notre position interne.",
            ))

        return proposals

    def leader_arbitrates(
        self,
        proposals: List[FactionProposal],
        adversary: Any,
    ) -> FactionProposal:
        """Le leader choisit selon sa personnalite"""
        if not proposals:
            # Fallback
            return FactionProposal(
                faction="politburo",
                action_type="consolidate",
                target_zone=None,
                target_country=None,
                intensity="light",
                rationale="No clear path forward.",
                rationale_fr="Aucune voie claire.",
            )

        # Trouver la proposition de chaque faction
        proposals_by_faction = {p.faction: p for p in proposals}

        # Personnalite du leader
        impulsivity = adversary.impulsivity
        risk_tolerance = adversary.risk_tolerance

        # Impulsif et risk-tolerant → ecoute l'Armee
        if impulsivity > 65 and risk_tolerance > 60:
            if "army" in proposals_by_faction:
                logger.debug("Leader arbitrage: Impulsif → Armee")
                return proposals_by_faction["army"]

        # Impulsif mais prudent → ecoute le KGB
        if impulsivity > 60 and risk_tolerance < 50:
            if "kgb" in proposals_by_faction:
                logger.debug("Leader arbitrage: Impulsif+Prudent → KGB")
                return proposals_by_faction["kgb"]

        # Prudent → ecoute le Politburo
        if impulsivity < 50:
            if "politburo" in proposals_by_faction:
                logger.debug("Leader arbitrage: Prudent → Politburo")
                return proposals_by_faction["politburo"]

        # Default : equilibre entre les propositions
        # Preferer Armee si opportunite, sinon KGB
        if adversary.doctrine.value in ["expansion", "destabilization"]:
            return proposals_by_faction.get("army") or proposals_by_faction.get("kgb") or proposals[0]
        else:
            return proposals_by_faction.get("politburo") or proposals_by_faction.get("kgb") or proposals[0]

    def record_error(
        self,
        turn: int,
        error_type: str,
        subject: str,
        belief: str,
        reality: str,
        consequence: str,
        consequence_fr: str,
        zone: Optional[str] = None,
        action_taken: Optional[str] = None,
        result: Optional[str] = None,
        escalation_delta: int = 0,
        factions: Optional[List[str]] = None,
    ):
        """
        Enregistre une erreur de l'IA pour le debrief.

        Args:
            turn: Tour ou l'erreur s'est produite
            error_type: Type d'erreur (overestimation, underestimation, misread_player, etc.)
            subject: Sujet de l'erreur (player_resolve, zone_stability, etc.)
            belief: Ce que l'IA croyait
            reality: Ce qui etait vrai
            consequence: Consequence en anglais (pour logs)
            consequence_fr: Consequence narrative en francais
            zone: Zone concernee (pour ancrage factuel)
            action_taken: Action prise suite a l'erreur
            result: Resultat de l'action (failed, partial, etc.)
            escalation_delta: Impact sur la tension
            factions: Factions impliquees (pour faction_conflict)
        """
        error = AIError(
            turn=turn,
            error_type=error_type,
            subject=subject,
            belief=belief,
            reality=reality,
            consequence=consequence,
            consequence_fr=consequence_fr,
            zone=zone,
            action_taken=action_taken,
            result=result,
            escalation_delta=escalation_delta,
            factions=factions,
        )
        self.errors.append(error)
        logger.info(f"AI Error recorded: {error_type} on {subject} (zone={zone})")

    def get_errors(self) -> List[AIError]:
        """Retourne les erreurs pour le debrief"""
        return self.errors

    def log_belief_vs_reality(
        self,
        beliefs: AIBeliefs,
        real_state: Any,
    ):
        """Compare croyances vs realite (debug only)"""
        logger.debug("=== BELIEF VS REALITY ===")
        logger.debug(f"Player resolve belief: {beliefs.player.resolve}")
        logger.debug(f"Player stability reality: {real_state.player.domestic_stability}")
        logger.debug(f"Nuclear risk belief: {beliefs.nuclear_risk}")
        logger.debug(f"DEFCON reality: {real_state.defcon}")

        for zone_id, zone_belief in beliefs.zones.items():
            if zone_id in real_state.zones:
                real_zone = real_state.zones[zone_id]
                logger.debug(f"""
                Zone {zone_id}:
                  Belief: stability={zone_belief.stability_band}, opp={zone_belief.opportunity_level}
                  Reality: stability={real_zone.stability}, control={real_zone.get_dominant_power()}
                  Confidence: {zone_belief.confidence}
                  Tags: {zone_belief.tags}
                """)
