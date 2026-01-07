"""Fronts Vivants v2 - Systeme base sur les ACTIONS, pas les metriques.

Chaque front affiche:
- Beat: le dernier signe marquant (action loggee)
- Mode dominant: soft/hard/covert/standoff (deduit des actions recentes)
- Omen: signal faible avant la crise
- Badge: etiquette visuelle (CRISE, OPERATION, SOMMET, RUMEUR)

Principe cle: montrer des "preuves" d'actions, pas des ecarts de metriques.
"""
import logging
import random
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from engine.narrative_state import NarrativeWorldState, ActionLogEntry, NarrativeZone

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class Band(str, Enum):
    """Quantification qualitative (pas de seuils magiques)"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# FRONT BEAT (dernier signe marquant)
# =============================================================================

class FrontBeat(BaseModel):
    """Le dernier signe marquant dans une zone.

    C'est la "preuve" visible de ce qui s'est passe.
    """
    kind: str       # "speech", "troops", "strike", "riot", "leak", "summit", "sanctions", "covert_op"
    actor: str      # "usa", "ussr", "local", "unknown"
    payload: str    # Mini-phrase brute ("navires en approche", "rumeur de putsch")
    freshness: int  # 0 = ce tour, 1 = tour precedent, etc.


# Mapping ActionType -> BeatKind
ACTION_TO_BEAT_KIND = {
    # Public actions
    "DIPLOMACY": "speech",
    "SPEECH": "speech",
    "SUMMIT": "summit",
    "PROPAGANDA": "speech",
    "SANCTIONS": "sanctions",
    "UN_SESSION": "speech",

    # Military actions
    "BLOCKADE": "troops",
    "MILITARY_POSTURE": "troops",
    "TROOPS": "troops",
    "NAVAL_ESCORT": "troops",
    "DEMO": "troops",

    # Covert actions
    "COVERT_OP": "covert_op",
    "INTEL_OP": "leak",
    "DESTABILIZE": "riot",
    "SUBMARINE_POSTURE": "covert_op",

    # Events
    "RUMOR": "leak",
    "RIOT": "riot",
    "STRIKE": "strike",

    # TEST choices
    "INTERCEPT_ORDER": "troops",
    "SHADOW_FLEET": "troops",
    "HOTLINE_CALL": "speech",

    # Aftershocks
    "GLOBAL_BACKLASH": "speech",
    "SUB_CONTACT_LOST": "covert_op",
}


# =============================================================================
# FRONT STATE
# =============================================================================

class FrontState(BaseModel):
    """Etat complet d'un front pour le FrontWall.

    Derive des actions, pas des metriques.
    """
    zone_id: str
    zone_name_fr: str

    # Mode dominant (deduit des actions recentes, pas des metriques)
    dominant_mode: str      # "soft", "hard", "covert", "standoff"

    # Tension (quantifiee en band, pas en chiffres)
    tension_band: Band

    # Spotlight (joueur ou IA a agi recemment)
    spotlight: bool

    # Crise
    has_crisis: bool

    # Beat (dernier signe marquant)
    beat: Optional[FrontBeat] = None

    # Surface phrase (generee depuis beat + etat)
    surface_phrase: str

    # Omen (signal faible pre-alarme)
    omen: Optional[str] = None      # "Bruit diplomatique", "Mouvements inhabituels", "Dernieres heures"

    # Badge UI
    badge: Optional[str] = None     # "CRISE", "OPERATION", "SOMMET", "RUMEUR", "DEPLOIEMENT"


# =============================================================================
# BEAT PHRASES (generation narrative depuis le beat)
# =============================================================================

BEAT_PHRASES: Dict[str, Dict[str, List[str]]] = {
    "troops": {
        "usa": [
            "Des convois traversent la nuit.",
            "La flotte se repositionne.",
            "Des navires de guerre prennent position.",
        ],
        "ussr": [
            "Des blindes ont ete reperes.",
            "Mouvements inhabituels a la frontiere.",
            "La flotte sovietique est en mouvement.",
        ],
        "local": [
            "L'armee locale se mobilise.",
            "Des troupes sont deployees.",
        ],
    },
    "covert_op": {
        "usa": [
            "Une operation discrete est en cours.",
            "Certains dossiers ont disparu.",
            "La CIA s'active.",
        ],
        "ussr": [
            "Le KGB s'active.",
            "Des agents ont ete identifies.",
            "Une operation secrete est en cours.",
        ],
        "unknown": [
            "Quelque chose se trame dans l'ombre.",
            "Des mouvements suspects ont ete signales.",
        ],
    },
    "leak": {
        "any": [
            "Une fuite circule. Trop precise pour etre un accident.",
            "Des documents ont ete transmis.",
            "Une rumeur persiste dans les cercles diplomatiques.",
        ],
    },
    "summit": {
        "any": [
            "Un sommet est annonce.",
            "Les delegations se preparent.",
            "Des negociations secretes sont en cours.",
        ],
    },
    "riot": {
        "local": [
            "Des manifestations eclatent.",
            "La rue gronde.",
            "L'agitation gagne les villes.",
        ],
        "any": [
            "Des troubles sont signales.",
            "La situation se tend.",
        ],
    },
    "speech": {
        "usa": [
            "Washington s'est exprime.",
            "Le President a fait une declaration.",
            "Un message officiel a ete transmis.",
        ],
        "ussr": [
            "Moscou a repondu.",
            "Le Kremlin s'est prononce.",
            "Khrouchtchev a fait une declaration.",
        ],
        "local": [
            "Les autorites locales ont reagi.",
            "Une conference de presse a eu lieu.",
        ],
    },
    "sanctions": {
        "any": [
            "Des sanctions ont ete annoncees.",
            "Des mesures economiques sont en place.",
            "L'embargo se durcit.",
        ],
    },
    "strike": {
        "any": [
            "Une frappe a ete ordonnee.",
            "Des objectifs ont ete touches.",
            "L'operation a commence.",
        ],
    },
}


# =============================================================================
# OMEN PHRASES (signaux faibles)
# =============================================================================

OMEN_PHRASES = {
    Band.CRITICAL: [
        "Dernieres heures",
        "Point de rupture",
        "Situation critique",
    ],
    Band.HIGH: [
        "Mouvements inhabituels",
        "Tension palpable",
        "Escalade en cours",
    ],
    Band.MEDIUM: [
        "Bruit diplomatique",
        "Signaux contradictoires",
        "Prudence requise",
    ],
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def to_band(value: float, max_val: float = 100) -> Band:
    """Quantize 0-max to band. Pas de seuils magiques exposes."""
    ratio = value / max_val if max_val > 0 else 0
    if ratio >= 0.75:
        return Band.CRITICAL
    elif ratio >= 0.5:
        return Band.HIGH
    elif ratio >= 0.25:
        return Band.MEDIUM
    return Band.LOW


def compute_dominant_mode(recent_actions: List["ActionLogEntry"]) -> str:
    """Deduit le mode dominant des actions des 3 derniers tours.

    Le mode est base sur les ACTIONS, pas sur des metriques.
    """
    if not recent_actions:
        return "standoff"

    mode_counts = {"soft": 0, "hard": 0, "covert": 0}

    for action in recent_actions:
        action_type = action.action_type
        if action_type in ["DIPLOMACY", "PROPAGANDA", "SUMMIT", "SPEECH", "UN_SESSION", "SANCTIONS"]:
            mode_counts["soft"] += 1
        elif action_type in ["MILITARY_POSTURE", "BLOCKADE", "TROOPS", "DEMO", "NAVAL_ESCORT",
                             "INTERCEPT_ORDER", "SHADOW_FLEET"]:
            mode_counts["hard"] += 1
        elif action_type in ["COVERT_OP", "INTEL_OP", "DESTABILIZE", "SUBMARINE_POSTURE"]:
            mode_counts["covert"] += 1

    # Le mode avec le plus d'actions recentes gagne
    max_mode = max(mode_counts, key=lambda k: mode_counts[k])
    if mode_counts[max_mode] == 0:
        return "standoff"
    return max_mode


def compute_tension_from_actions(recent_actions: List["ActionLogEntry"]) -> Band:
    """Calcule la tension depuis la cadence et gravite des actions.

    Pas de metriques brutes: on compte les actions et leur intensite.
    """
    if not recent_actions:
        return Band.LOW

    # Score base sur l'intensite des actions
    intensity_score = {"light": 1, "moderate": 2, "heavy": 3}
    total_score = 0

    for action in recent_actions:
        total_score += intensity_score.get(action.intensity, 1)

    # Normaliser sur 10 points max (3 actions heavy = 9)
    normalized = min(total_score / 10.0, 1.0)

    if normalized >= 0.7:
        return Band.CRITICAL
    elif normalized >= 0.4:
        return Band.HIGH
    elif normalized >= 0.2:
        return Band.MEDIUM
    return Band.LOW


def create_front_beat(action: "ActionLogEntry", current_turn: int) -> FrontBeat:
    """Cree un FrontBeat depuis une ActionLogEntry."""
    beat_kind = ACTION_TO_BEAT_KIND.get(action.action_type, "speech")

    return FrontBeat(
        kind=beat_kind,
        actor=action.actor,
        payload=action.payload_fr,
        freshness=current_turn - action.turn,
    )


def generate_surface_phrase(beat: Optional[FrontBeat], tension: Band, has_crisis: bool) -> str:
    """Genere une phrase depuis le beat + tension.

    C'est la phrase affichee dans le FrontWall.
    """
    if beat is None:
        if has_crisis:
            return "La crise couve. Aucun mouvement visible."
        return "Calme apparent."

    # Chercher une phrase dans le pool
    phrases = BEAT_PHRASES.get(beat.kind, {})
    actor_phrases = phrases.get(beat.actor) or phrases.get("any", [beat.payload])

    if not actor_phrases:
        base = beat.payload
    else:
        base = random.choice(actor_phrases)

    # Ajouter une coloration selon la tension
    if tension == Band.CRITICAL:
        return f"{base} Le temps presse."
    elif tension == Band.HIGH:
        return f"{base} La tension monte."
    return base


def compute_omen(tension: Band, has_crisis: bool) -> Optional[str]:
    """Signal faible avant la crise."""
    if has_crisis:
        return random.choice(OMEN_PHRASES[Band.CRITICAL])
    elif tension == Band.CRITICAL:
        return random.choice(OMEN_PHRASES[Band.CRITICAL])
    elif tension == Band.HIGH:
        return random.choice(OMEN_PHRASES[Band.HIGH])
    elif tension == Band.MEDIUM:
        return random.choice(OMEN_PHRASES[Band.MEDIUM])
    return None


def compute_badge(beat: Optional[FrontBeat], has_crisis: bool, recent_actions: List["ActionLogEntry"]) -> Optional[str]:
    """Badge UI selon le type d'activite."""
    if has_crisis:
        return "CRISE"

    if beat is None:
        return None

    badge_map = {
        "summit": "SOMMET",
        "covert_op": "OPERATION",
        "leak": "RUMEUR",
        "troops": "DEPLOIEMENT",
        "sanctions": "SANCTIONS",
        "riot": "TENSIONS",
        "strike": "FRAPPE",
    }
    return badge_map.get(beat.kind)


# =============================================================================
# FONCTION PRINCIPALE: BUILD FRONT STATE
# =============================================================================

def build_front_state(
    zone: "NarrativeZone",
    world_state: "NarrativeWorldState",
) -> FrontState:
    """Construit le FrontState pour une zone.

    Base sur les ACTIONS loggees, pas sur les metriques.
    """
    zone_id = zone.id
    current_turn = world_state.turn

    # Recuperer les actions recentes (3 derniers tours)
    recent_actions = world_state.get_recent_actions(zone_id=zone_id, lookback_turns=3)

    # Dernier beat
    last_action = world_state.get_last_beat(zone_id)
    beat = create_front_beat(last_action, current_turn) if last_action else None

    # Mode dominant (soft/hard/covert/standoff)
    dominant_mode = compute_dominant_mode(recent_actions)

    # Tension depuis les actions (pas depuis les metriques)
    tension_band = compute_tension_from_actions(recent_actions)

    # Si la zone a une crise, forcer CRITICAL
    if zone.has_crisis:
        tension_band = Band.CRITICAL

    # Spotlight = activite recente (2 derniers tours)
    active_zones = world_state.get_zones_with_activity(lookback_turns=2)
    spotlight = zone_id in active_zones

    # Omen
    omen = compute_omen(tension_band, zone.has_crisis)

    # Badge
    badge = compute_badge(beat, zone.has_crisis, recent_actions)

    # Surface phrase
    surface_phrase = generate_surface_phrase(beat, tension_band, zone.has_crisis)

    return FrontState(
        zone_id=zone_id,
        zone_name_fr=zone.name_fr,
        dominant_mode=dominant_mode,
        tension_band=tension_band,
        spotlight=spotlight,
        has_crisis=zone.has_crisis,
        beat=beat,
        surface_phrase=surface_phrase,
        omen=omen,
        badge=badge,
    )


# =============================================================================
# SELECTION DES FRONTS A AFFICHER
# =============================================================================

def select_fronts(all_fronts: List[FrontState], max_display: int = 6) -> List[FrontState]:
    """Selection dynamique des fronts a afficher.

    Pas "5 fixes + crises". Le mur reflete la partie actuelle.
    """
    selected = []

    # 1. Toujours: fronts en crise
    for f in all_fronts:
        if f.has_crisis:
            selected.append(f)

    # 2. Fronts avec spotlight (action recente joueur/IA)
    for f in all_fronts:
        if f.spotlight and f not in selected:
            selected.append(f)

    # 3. Completer avec strategiques si besoin
    strategic_order = ["central_america", "europe_west", "middle_east", "turkey_greece", "southeast_asia", "europe_east"]
    for zone_id in strategic_order:
        if len(selected) >= max_display:
            break
        for f in all_fronts:
            if f.zone_id == zone_id and f not in selected:
                selected.append(f)

    # Tri: crises > spotlight > autres
    selected.sort(key=lambda f: (
        0 if f.has_crisis else 1,
        0 if f.spotlight else 1,
        f.tension_band.value,  # CRITICAL < HIGH < MEDIUM < LOW (alphabetique inverse)
    ))

    return selected[:max_display]


# =============================================================================
# API PRINCIPALE: GET ALL FRONTS
# =============================================================================

def get_all_fronts(world_state: "NarrativeWorldState") -> List[FrontState]:
    """Construit les FrontState pour toutes les zones.

    Appele par l'API /fronts.
    """
    all_fronts = []
    for zone in world_state.zones.values():
        front = build_front_state(zone, world_state)
        all_fronts.append(front)
    return all_fronts


def get_display_fronts(world_state: "NarrativeWorldState", max_display: int = 6) -> List[FrontState]:
    """Recupere les fronts a afficher dans le FrontWall.

    Appele par l'API /fronts pour le rendu UI.
    """
    all_fronts = get_all_fronts(world_state)
    return select_fronts(all_fronts, max_display)
