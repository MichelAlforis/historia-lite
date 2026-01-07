"""
Silence Mechanics - "L'Histoire n'attend pas"

Quand le chef d'Etat ne decide pas, le systeme choisit un acteur qui comble le vide.
Pas de jauge lineaire previsible. Des triggers conditionnels + suspense.

PHILOSOPHIE:
- Le silence est un signal, pas une erreur
- On ne renverse pas le joueur, on reduit sa marge de manoeuvre
- Les acteurs autonomes dependent du regime et du contexte
- Le joueur ne sait pas QUAND ca va exploser, mais il sait que ca VA exploser

ACTEURS QUI COMBLENT LE VIDE:
- USA: Congress, Pentagon, CIA, State Department, Media
- USSR: Politburo, KGB, Etat-major, Appareil du Parti, Propagande
"""
import logging
import random
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AutonomousActor(str, Enum):
    """Acteurs qui peuvent agir sans le joueur"""
    # USA
    CONGRESS = "congress"
    PENTAGON = "pentagon"
    CIA = "cia"
    STATE_DEPT = "state_dept"
    MEDIA_US = "media_us"

    # USSR
    POLITBURO = "politburo"
    KGB = "kgb"
    RED_ARMY = "red_army"
    PARTY_APPARATUS = "party_apparatus"
    PRAVDA = "pravda"


class SilenceEventType(str, Enum):
    """Types d'evenements declenches par le silence"""
    WARNING = "warning"                 # Conseiller insiste (soft)
    AUTONOMOUS_ACTION = "autonomous"    # Acteur prend initiative
    LEAK = "leak"                       # Fuite / revelation
    FAIT_ACCOMPLI = "fait_accompli"     # Decision prise sans toi
    PUBLIC_CRISIS = "public_crisis"     # Opinion publique reagit
    LOSS_OF_CONTROL = "loss_of_control" # Perte de marge de manoeuvre


@dataclass
class SilenceEvent:
    """Evenement declenche par l'inactivite du joueur"""
    id: str
    type: SilenceEventType
    actor: AutonomousActor
    title_fr: str
    description_fr: str
    effects: Dict[str, Any] = field(default_factory=dict)
    is_reversible: bool = True
    urgency: str = "high"  # low, medium, high, critical

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "actor": self.actor.value,
            "title_fr": self.title_fr,
            "description_fr": self.description_fr,
            "effects": self.effects,
            "is_reversible": self.is_reversible,
            "urgency": self.urgency,
        }


@dataclass
class SilenceState:
    """Etat du silence / inactivite du joueur"""
    silence_streak: int = 0              # Tours consecutifs sans action
    ignored_dossiers: List[str] = field(default_factory=list)  # IDs des dossiers ignores
    last_action_turn: int = 0            # Dernier tour avec action
    total_empty_jumps: int = 0           # Total de jumps vides
    pressure_cards: int = 0              # "Cartes" de pression accumulees
    triggered_events: List[str] = field(default_factory=list)  # Events deja declenches

    def to_dict(self) -> Dict:
        return {
            "silence_streak": self.silence_streak,
            "ignored_dossiers_count": len(self.ignored_dossiers),
            "last_action_turn": self.last_action_turn,
            "total_empty_jumps": self.total_empty_jumps,
            "pressure_cards": self.pressure_cards,
        }


# =============================================================================
# TRIGGERS CONDITIONNELS
# =============================================================================

@dataclass
class SilenceTrigger:
    """Condition qui declenche un evenement de silence"""
    id: str
    name: str

    # Conditions (toutes doivent etre vraies)
    min_silence_streak: int = 0
    min_ignored_dossiers: int = 0
    min_pressure_cards: int = 0
    requires_crisis: bool = False
    requires_high_tension: bool = False  # world_tension > 60
    requires_low_stability: bool = False  # domestic_stability < 40
    requires_dossier_type: Optional[str] = None  # crisis, threat, etc.

    # Probabilite de declenchement si conditions remplies (0-100)
    trigger_chance: int = 50

    # Ce qui se passe
    event_type: SilenceEventType = SilenceEventType.WARNING
    actor_us: AutonomousActor = AutonomousActor.CONGRESS
    actor_ussr: AutonomousActor = AutonomousActor.POLITBURO

    # Template narratif
    title_template_us: str = ""
    title_template_ussr: str = ""
    description_template_us: str = ""
    description_template_ussr: str = ""

    # Effets
    effects: Dict[str, Any] = field(default_factory=dict)


# Pool de triggers (combinaisons qui declenchent des evenements)
SILENCE_TRIGGERS: List[SilenceTrigger] = [
    # ---------------------------------------------------------------------------
    # NIVEAU 1: Avertissements (soft)
    # ---------------------------------------------------------------------------
    SilenceTrigger(
        id="advisor_nudge",
        name="Conseiller insiste",
        min_silence_streak=1,
        min_ignored_dossiers=1,
        trigger_chance=70,
        event_type=SilenceEventType.WARNING,
        actor_us=AutonomousActor.STATE_DEPT,
        actor_ussr=AutonomousActor.PARTY_APPARATUS,
        title_template_us="Votre conseiller s'impatiente",
        title_template_ussr="Le Parti attend vos directives",
        description_template_us="Le Secretaire d'Etat demande une audience urgente.",
        description_template_ussr="Le Comite Central s'interroge sur votre silence.",
        effects={},
    ),

    # ---------------------------------------------------------------------------
    # NIVEAU 2: Initiatives autonomes (medium)
    # ---------------------------------------------------------------------------
    SilenceTrigger(
        id="military_posture",
        name="Posture militaire autonome",
        min_silence_streak=2,
        requires_crisis=True,
        requires_high_tension=True,
        trigger_chance=60,
        event_type=SilenceEventType.AUTONOMOUS_ACTION,
        actor_us=AutonomousActor.PENTAGON,
        actor_ussr=AutonomousActor.RED_ARMY,
        title_template_us="Le Pentagone a pris les devants",
        title_template_ussr="L'Etat-major a place les forces en alerte",
        description_template_us="Face a votre silence, le Commandement a rehausse le niveau d'alerte. Vous n'avez pas ete consulte.",
        description_template_ussr="Le Marechal a juge prudent de preparer les forces. On vous informe apres coup.",
        effects={"world_tension": 10, "defcon_risk": True},
    ),

    SilenceTrigger(
        id="intel_action",
        name="Action de renseignement autonome",
        min_silence_streak=2,
        min_ignored_dossiers=2,
        trigger_chance=50,
        event_type=SilenceEventType.AUTONOMOUS_ACTION,
        actor_us=AutonomousActor.CIA,
        actor_ussr=AutonomousActor.KGB,
        title_template_us="La CIA a pris une initiative",
        title_template_ussr="Le KGB a 'securise' la situation",
        description_template_us="Langley a lance une operation sans votre feu vert. Les resultats vous seront presentes demain.",
        description_template_ussr="Le Camarade Directeur vous informe que des 'mesures de securite' ont ete prises.",
        effects={"intel_exposure": 15},
    ),

    # ---------------------------------------------------------------------------
    # NIVEAU 3: Faits accomplis (hard)
    # ---------------------------------------------------------------------------
    SilenceTrigger(
        id="diplomatic_bypass",
        name="Court-circuit diplomatique",
        min_silence_streak=3,
        requires_dossier_type="summit",
        trigger_chance=70,
        event_type=SilenceEventType.FAIT_ACCOMPLI,
        actor_us=AutonomousActor.STATE_DEPT,
        actor_ussr=AutonomousActor.POLITBURO,
        title_template_us="Le Departement d'Etat a negocie sans vous",
        title_template_ussr="Le Politburo a tranche",
        description_template_us="Un accord preliminaire a ete signe en votre nom. Vous decouvrez les termes dans la presse.",
        description_template_ussr="Une decision collegiale a ete prise. Vous etes informe par communique interne.",
        effects={"political_capital": -10, "international_reputation": -5},
    ),

    SilenceTrigger(
        id="crisis_escalation_auto",
        name="Escalade automatique",
        min_silence_streak=2,
        requires_crisis=True,
        min_pressure_cards=3,
        trigger_chance=80,
        event_type=SilenceEventType.FAIT_ACCOMPLI,
        actor_us=AutonomousActor.PENTAGON,
        actor_ussr=AutonomousActor.RED_ARMY,
        title_template_us="La situation a echappe a votre controle",
        title_template_ussr="Les evenements ont devance vos ordres",
        description_template_us="Pendant votre hesitation, l'escalade s'est poursuivie. Les options se reduisent.",
        description_template_ussr="Le temps de la reflexion est passe. Les faits sont accomplis.",
        effects={"world_tension": 15, "stability": -10},
    ),

    # ---------------------------------------------------------------------------
    # NIVEAU 4: Fuites et crises publiques
    # ---------------------------------------------------------------------------
    SilenceTrigger(
        id="media_leak",
        name="Fuite mediatique",
        min_silence_streak=2,
        min_ignored_dossiers=3,
        trigger_chance=55,
        event_type=SilenceEventType.LEAK,
        actor_us=AutonomousActor.MEDIA_US,
        actor_ussr=AutonomousActor.PRAVDA,
        title_template_us="Fuite dans la presse",
        title_template_ussr="Rumeurs dans les couloirs du Kremlin",
        description_template_us="Le Washington Post publie des 'sources proches de la Maison Blanche' qui s'inquietent de votre inaction.",
        description_template_ussr="La Pravda publie un editorial sur 'la vigilance revolutionnaire'. Le message est clair.",
        effects={"domestic_stability": -10, "international_reputation": -5},
    ),

    SilenceTrigger(
        id="public_pressure",
        name="Pression publique",
        min_silence_streak=3,
        requires_low_stability=True,
        trigger_chance=65,
        event_type=SilenceEventType.PUBLIC_CRISIS,
        actor_us=AutonomousActor.CONGRESS,
        actor_ussr=AutonomousActor.PARTY_APPARATUS,
        title_template_us="Le Congres s'impatiente",
        title_template_ussr="Le Parti gronde",
        description_template_us="Des senateurs demandent publiquement des explications sur votre gestion de la crise.",
        description_template_ussr="Des rapports font etat de 'preoccupations' au sein du Comite Central.",
        effects={"domestic_stability": -15, "political_capital": -10},
    ),

    # ---------------------------------------------------------------------------
    # NIVEAU 5: Perte de controle (extreme)
    # ---------------------------------------------------------------------------
    SilenceTrigger(
        id="loss_of_initiative",
        name="Perte d'initiative",
        min_silence_streak=4,
        min_pressure_cards=5,
        requires_high_tension=True,
        trigger_chance=90,
        event_type=SilenceEventType.LOSS_OF_CONTROL,
        actor_us=AutonomousActor.PENTAGON,
        actor_ussr=AutonomousActor.POLITBURO,
        title_template_us="Vous avez perdu l'initiative",
        title_template_ussr="L'initiative vous echappe",
        description_template_us="Vos conseillers agissent desormais en votre nom. Vous pouvez reprendre le controle, mais il faudra s'imposer.",
        description_template_ussr="Le Politburo prend les decisions urgentes. Vous restez informe, mais plus consulte.",
        effects={"political_capital": -20, "action_capacity": -1},
    ),
]


# =============================================================================
# MOTEUR DE SILENCE
# =============================================================================

def check_silence_triggers(
    silence_state: SilenceState,
    world_state: Any,  # NarrativeWorldState
    is_ussr: bool = False,
) -> List[SilenceEvent]:
    """
    Verifie les triggers et retourne les evenements a declencher.

    Args:
        silence_state: Etat du silence du joueur
        world_state: Etat du monde (defcon, tension, crises, etc.)
        is_ussr: True si le joueur joue l'URSS

    Returns:
        Liste d'evenements de silence a afficher
    """
    triggered_events: List[SilenceEvent] = []

    # Extraire les donnees du world_state
    world_tension = getattr(world_state, 'world_tension', 50)
    domestic_stability = getattr(world_state, 'player', {})
    if hasattr(domestic_stability, 'domestic_stability'):
        domestic_stability = domestic_stability.domestic_stability
    else:
        domestic_stability = 60

    # Verifier s'il y a des crises actives
    has_crisis = False
    crisis_types = set()
    for zone in getattr(world_state, 'zones', {}).values():
        if getattr(zone, 'has_crisis', False):
            has_crisis = True
        if getattr(zone, 'stability', 100) < 30:
            has_crisis = True

    # Verifier les dossiers ignores
    dossier_types = set(silence_state.ignored_dossiers)

    for trigger in SILENCE_TRIGGERS:
        # Skip si deja declenche ce tour
        if trigger.id in silence_state.triggered_events:
            continue

        # Verifier toutes les conditions
        if not _check_trigger_conditions(
            trigger,
            silence_state,
            world_tension,
            domestic_stability,
            has_crisis,
            dossier_types,
        ):
            continue

        # Test de probabilite
        if random.randint(1, 100) > trigger.trigger_chance:
            continue

        # Creer l'evenement
        actor = trigger.actor_ussr if is_ussr else trigger.actor_us
        title = trigger.title_template_ussr if is_ussr else trigger.title_template_us
        description = trigger.description_template_ussr if is_ussr else trigger.description_template_us

        event = SilenceEvent(
            id=f"silence_{trigger.id}_{silence_state.silence_streak}",
            type=trigger.event_type,
            actor=actor,
            title_fr=title,
            description_fr=description,
            effects=trigger.effects.copy(),
            is_reversible=trigger.event_type != SilenceEventType.LOSS_OF_CONTROL,
            urgency="critical" if trigger.event_type in [
                SilenceEventType.FAIT_ACCOMPLI,
                SilenceEventType.LOSS_OF_CONTROL
            ] else "high",
        )

        triggered_events.append(event)
        silence_state.triggered_events.append(trigger.id)

        logger.info(f"Silence trigger activated: {trigger.name} -> {event.title_fr}")

        # Limiter a 2 evenements par tour pour ne pas submerger
        if len(triggered_events) >= 2:
            break

    return triggered_events


def _check_trigger_conditions(
    trigger: SilenceTrigger,
    silence_state: SilenceState,
    world_tension: int,
    domestic_stability: int,
    has_crisis: bool,
    dossier_types: set,
) -> bool:
    """Verifie si toutes les conditions d'un trigger sont remplies"""

    if silence_state.silence_streak < trigger.min_silence_streak:
        return False

    if len(silence_state.ignored_dossiers) < trigger.min_ignored_dossiers:
        return False

    if silence_state.pressure_cards < trigger.min_pressure_cards:
        return False

    if trigger.requires_crisis and not has_crisis:
        return False

    if trigger.requires_high_tension and world_tension <= 60:
        return False

    if trigger.requires_low_stability and domestic_stability >= 40:
        return False

    if trigger.requires_dossier_type:
        if trigger.requires_dossier_type not in dossier_types:
            return False

    return True


def update_silence_state(
    silence_state: SilenceState,
    action_count: int,
    ignored_dossier_ids: List[str],
    current_turn: int,
) -> None:
    """
    Met a jour l'etat du silence apres un jump.

    Args:
        silence_state: Etat a modifier
        action_count: Nombre d'actions dans la queue
        ignored_dossier_ids: IDs des dossiers non traites
        current_turn: Tour actuel
    """
    if action_count == 0:
        # Jump vide
        silence_state.silence_streak += 1
        silence_state.total_empty_jumps += 1
        # Ajouter des cartes de pression (non-lineaire)
        cards_to_add = 1 + len(ignored_dossier_ids) // 2
        silence_state.pressure_cards += cards_to_add
        logger.debug(f"Empty jump: streak={silence_state.silence_streak}, cards+={cards_to_add}")
    else:
        # Le joueur a agi
        silence_state.silence_streak = 0
        silence_state.last_action_turn = current_turn
        # Reduire la pression (mais pas a zero immediatement)
        silence_state.pressure_cards = max(0, silence_state.pressure_cards - 2)
        # Clear triggered events pour permettre re-declenchement
        silence_state.triggered_events = []

    # Mettre a jour les dossiers ignores
    silence_state.ignored_dossiers = ignored_dossier_ids


def apply_silence_effects(
    world_state: Any,
    events: List[SilenceEvent],
) -> List[str]:
    """
    Applique les effets des evenements de silence au monde.

    Returns:
        Liste de messages narratifs
    """
    messages = []

    for event in events:
        effects = event.effects

        # Appliquer les effets avec diminishing returns sur la tension
        if "world_tension" in effects:
            delta = effects["world_tension"]
            # Diminishing returns: plus la tension est haute, moins chaque point pousse
            damping = max(0.25, 1.0 - (world_state.world_tension / 140.0))
            effective_delta = int(round(delta * damping))
            world_state.world_tension = min(100, max(0, world_state.world_tension + effective_delta))
            messages.append(f"Tension mondiale: {'+' if effective_delta > 0 else ''}{effective_delta}")

        if "political_capital" in effects:
            delta = effects["political_capital"]
            world_state.player.political_capital = max(0, world_state.player.political_capital + delta)
            messages.append(f"Capital politique: {'+' if delta > 0 else ''}{delta}")

        if "domestic_stability" in effects:
            delta = effects["domestic_stability"]
            world_state.player.domestic_stability = max(0, min(100, world_state.player.domestic_stability + delta))

        if "international_reputation" in effects:
            delta = effects["international_reputation"]
            world_state.player.international_reputation = max(0, min(100, world_state.player.international_reputation + delta))

        if "intel_exposure" in effects:
            delta = effects["intel_exposure"]
            world_state.player.intel_exposure = min(100, world_state.player.intel_exposure + delta)

        # action_capacity is computed from political_capital, so reduce capital instead
        if "action_capacity" in effects:
            delta = effects["action_capacity"]
            # Each capacity point = ~15 political capital reduction
            capital_delta = delta * 15
            world_state.player.political_capital = max(0, min(100, world_state.player.political_capital + capital_delta))

        logger.info(f"Applied silence effects: {event.id} -> {effects}")

    return messages


# =============================================================================
# PHRASES NARRATIVES POUR LE SILENCE
# =============================================================================

SILENCE_NARRATIVES = {
    "empty_jump_mild": [
        "Vous n'avez donne aucune instruction.",
        "Le monde a continue sans vous.",
        "Votre silence a ete note.",
    ],
    "empty_jump_tense": [
        "Pendant que vous hezitiez, le monde n'a pas attendu.",
        "Votre inaction a ete interpretee.",
        "D'autres ont pris les decisions a votre place.",
    ],
    "empty_jump_critical": [
        "L'Histoire n'attend pas que le chef d'Etat soit inspire.",
        "Votre silence est devenu une reponse.",
        "Ne rien faire, c'est laisser d'autres ecrire l'histoire.",
    ],
}


def get_silence_narrative(silence_streak: int, world_tension: int) -> str:
    """Retourne une phrase narrative pour un jump vide"""
    if world_tension > 70 or silence_streak >= 3:
        pool = SILENCE_NARRATIVES["empty_jump_critical"]
    elif world_tension > 50 or silence_streak >= 2:
        pool = SILENCE_NARRATIVES["empty_jump_tense"]
    else:
        pool = SILENCE_NARRATIVES["empty_jump_mild"]

    return random.choice(pool)


# =============================================================================
# INTENTION COOLDOWN - Resistance narrative aux actions repetees
# =============================================================================
# Quand le joueur spam la meme intention, les acteurs reagissent:
# - Conseillers sceptiques
# - Adversaire percoit une faiblesse ou une obsession
# - Beats deviennent "ca ne suffit plus"
#
# PAS DE MALUS MECANIQUE - juste une resistance qualitative

@dataclass
class IntentionCooldown:
    """Tracker de repetition d'intentions"""
    intention_history: Dict[str, int] = field(default_factory=dict)  # intention_type -> count
    last_turn_used: Dict[str, int] = field(default_factory=dict)  # intention_type -> turn

    def record_intention(self, intention_type: str, current_turn: int):
        """Enregistre une intention utilisee"""
        # Categorie principale (DIPLO, MIL, COV, etc.)
        category = intention_type.split("_")[0] if "_" in intention_type else intention_type

        self.intention_history[category] = self.intention_history.get(category, 0) + 1
        self.last_turn_used[category] = current_turn

    def get_repetition_count(self, intention_type: str) -> int:
        """Nombre de fois que cette categorie a ete utilisee"""
        category = intention_type.split("_")[0] if "_" in intention_type else intention_type
        return self.intention_history.get(category, 0)

    def is_spammed(self, intention_type: str, threshold: int = 3) -> bool:
        """True si l'intention est repetee au-dela du seuil"""
        return self.get_repetition_count(intention_type) >= threshold

    def to_dict(self) -> Dict:
        return {
            "intention_history": self.intention_history,
            "last_turn_used": self.last_turn_used,
        }


# Narratifs de resistance quand une intention est spammee
COOLDOWN_NARRATIVES = {
    # Conseillers sceptiques
    "advisor_skeptical": [
        "Vos conseillers echangent des regards. 'Encore?' semble dire leur silence.",
        "Le Secretaire d'Etat hesite avant de transmettre. Il sait ce que vous allez dire.",
        "Les officiels executent, mais l'enthousiasme n'y est plus.",
        "'Monsieur le President, nous avons deja essaye cela trois fois.'",
    ],

    # Adversaire percoit une obsession
    "adversary_reads_pattern": [
        "Moscou a remarque votre preference. Ils s'adaptent.",
        "Le Kremlin sait maintenant ce que vous allez faire. Ils l'attendent.",
        "Khrouchtchev sourit en lisant vos actions. Vous etes devenu previsible.",
        "Les analystes sovietiques ont identifie votre pattern. Le jeu a change.",
    ],

    # Beats "ca ne suffit plus"
    "diminishing_narrative": [
        "L'impact n'est plus le meme. Le monde s'habitue.",
        "Ce qui impressionnait hier fait hausser les epaules aujourd'hui.",
        "La repetition affaiblit le message. Ils ont deja entendu ca.",
        "L'effet de surprise est passe. Maintenant, c'est juste du bruit.",
    ],
}


def get_cooldown_narrative(intention_type: str, repetition_count: int) -> Optional[str]:
    """
    Retourne un narratif de resistance si l'intention est repetee.

    Ne change PAS la mecanique - juste un feedback qualitatif.

    Args:
        intention_type: Type d'intention (MIL_BLOCKADE, DIPLO_SUMMIT, etc.)
        repetition_count: Nombre de fois utilisee

    Returns:
        String narratif ou None si pas de cooldown
    """
    if repetition_count < 3:
        return None  # Pas de cooldown avant 3 utilisations

    if repetition_count == 3:
        # Premier avertissement - conseiller sceptique
        return random.choice(COOLDOWN_NARRATIVES["advisor_skeptical"])
    elif repetition_count == 4:
        # Adversaire percoit le pattern
        return random.choice(COOLDOWN_NARRATIVES["adversary_reads_pattern"])
    else:
        # 5+ : impact diminue narrativement
        return random.choice(COOLDOWN_NARRATIVES["diminishing_narrative"])


def check_intention_cooldown(
    intention_type: str,
    cooldown_state: IntentionCooldown,
    current_turn: int,
) -> Tuple[bool, Optional[str]]:
    """
    Verifie si une intention est en cooldown et retourne le feedback.

    Args:
        intention_type: Type d'intention
        cooldown_state: Etat du cooldown
        current_turn: Tour actuel

    Returns:
        (is_cooled_down, narrative_feedback)
    """
    repetition_count = cooldown_state.get_repetition_count(intention_type)
    is_spammed = repetition_count >= 3

    if is_spammed:
        narrative = get_cooldown_narrative(intention_type, repetition_count)
        return True, narrative

    return False, None
