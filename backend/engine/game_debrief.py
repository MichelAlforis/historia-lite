"""
Game Debrief - Analyse narrative post-defaite

Genere un debrief narratif qui explique POURQUOI le joueur a perdu,
sans jamais montrer de chiffres. Juste une lecture historique.

> "Votre silence sur Cuba a laisse l'armee agir.
> Votre fermete a Berlin a isole vos allies.
> Le monde a glisse."

PHILOSOPHIE:
- Pas de blame ("vous avez fait X erreurs")
- Pas de chiffres ("stabilite -45")
- Juste une lecture historique narrative
- Le joueur comprend a posteriori, pas pendant

UTILISE:
- NarrativeWorldState pour l'etat du monde
- SilenceState pour l'historique du silence
- NarrativeOrchestrator pour generer les scenes
"""
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum

from engine.narrative_orchestrator import (
    NarrativeScene,
    LeaderDialogue,
    PressHeadline,
    WORLD_LEADERS,
    ZONE_NAMES_FR,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CAUSE TYPES
# =============================================================================

class CauseCategory(str, Enum):
    """Categories de causes de defaite"""
    SILENCE = "silence"           # Inaction repetee
    ESCALATION = "escalation"     # Escalade militaire
    PROVOCATION = "provocation"   # Action trop agressive
    OMISSION = "omission"         # Dossier ignore
    ISOLATION = "isolation"       # Allies perdus
    INSTABILITY = "instability"   # Crise interne
    MISCALCULATION = "miscalc"    # Erreur de calcul


@dataclass
class DebriefCause:
    """Une decision cle ayant mene a la defaite"""
    turn: int                           # Tour ou c'est arrive
    category: CauseCategory             # Type de cause
    zone: Optional[str] = None          # Zone concernee
    actor: Optional[str] = None         # Acteur implique
    narrative_fr: str = ""              # Phrase narrative
    contributed_to: str = ""            # "coup", "apocalypse", etc.
    severity: str = "medium"            # low, medium, high, critical

    def to_dict(self) -> Dict:
        return {
            "turn": self.turn,
            "category": self.category.value,
            "zone": self.zone,
            "zone_name_fr": ZONE_NAMES_FR.get(self.zone, self.zone) if self.zone else None,
            "actor": self.actor,
            "narrative_fr": self.narrative_fr,
            "contributed_to": self.contributed_to,
            "severity": self.severity,
        }


@dataclass
class AIStrategicError:
    """Une erreur strategique de l'IA adversaire (pour le debrief)"""
    turn: int
    error_type: str                     # overestimation, underestimation, misread
    belief_fr: str                      # Ce que l'IA croyait (en francais)
    reality_fr: str                     # La realite
    consequence_fr: str                 # Consequence narrative

    def to_dict(self) -> Dict:
        return {
            "turn": self.turn,
            "error_type": self.error_type,
            "belief_fr": self.belief_fr,
            "reality_fr": self.reality_fr,
            "consequence_fr": self.consequence_fr,
        }


@dataclass
class GameDebrief:
    """Debrief complet de fin de partie"""
    end_reason: str                     # apocalypse, coup_etat, defeat_honorable
    victory: bool                       # True si victoire
    title_fr: str = ""                  # Titre dramatique
    narrative_fr: str = ""              # Recit principal
    causes: List[DebriefCause] = field(default_factory=list)
    leader_dialogue: Optional[LeaderDialogue] = None
    press_headlines: List[PressHeadline] = field(default_factory=list)
    final_state_summary: Dict[str, str] = field(default_factory=dict)
    ai_errors: List[AIStrategicError] = field(default_factory=list)  # Erreurs de l'IA

    def to_dict(self) -> Dict:
        result = {
            "end_reason": self.end_reason,
            "victory": self.victory,
            "title_fr": self.title_fr,
            "narrative_fr": self.narrative_fr,
            "causes": [c.to_dict() for c in self.causes],
            "final_state_summary": self.final_state_summary,
        }
        if self.leader_dialogue:
            result["leader_dialogue"] = self.leader_dialogue.to_dict()
        if self.press_headlines:
            result["press_headlines"] = [p.to_dict() for p in self.press_headlines]
        if self.ai_errors:
            result["ai_errors"] = [e.to_dict() for e in self.ai_errors]
        return result


# =============================================================================
# DEFEAT TITLES
# =============================================================================

DEFEAT_TITLES = {
    "apocalypse": "Le monde n'est plus que cendres",
    "coup_etat": "Le gouvernement a ete renverse",
    "defeat_honorable": "L'Histoire a choisi l'autre camp",
    "domination": "Le monde libre triomphe",
    "survival": "La paix, enfin",
    "adversary_collapse": "L'empire s'effondre",
}

DEFEAT_NARRATIVES = {
    "apocalypse": [
        "Le blocus de Cuba etait un pari. Khrouchtchev n'a pas cede. "
        "Vous avez mobilise les B-52. Ils ont arme leurs ICBM. "
        "Personne n'a recule. Personne ne pouvait.",

        "Les lignes rouges se sont croisees. Les ultimatums sont restes sans reponse. "
        "Quelque part au-dessus du Pacifique, un missile a franchi le point de non-retour. "
        "Le reste n'est que cendres.",

        "L'escalade semblait maitrisee. Chaque camp croyait que l'autre reculerait. "
        "Ils avaient tort tous les deux. L'Histoire retiendra que personne n'a voulu ceder."
    ],
    "coup_etat": [
        "Votre silence sur Cuba a laisse l'armee agir sans supervision. "
        "Les generaux ont vu le vide au sommet de l'Etat. "
        "Ce matin, votre gouvernement n'existe plus.",

        "Le Congres s'est impatiente. Le Pentagon a pris les devants. "
        "Quand vous avez voulu reprendre la main, il etait trop tard. "
        "L'ordre constitutionnel a ete suspendu 'temporairement'.",

        "Votre inaction a ete interpretee comme de la faiblesse. "
        "D'autres ont decide que le pays avait besoin d'un chef plus ferme. "
        "L'Histoire vous jugera... si on la laisse s'ecrire."
    ],
    "defeat_honorable": [
        "Vous avez tenu. Pas assez. "
        "Zone apres zone, l'influence s'est erodee. "
        "En 1991, le monde est bipolaire. Mais le pole, c'est Moscou.",

        "La Guerre Froide est terminee. Vous avez perdu. "
        "Non pas par un grand fracas, mais par l'usure du temps. "
        "L'adversaire a ete plus patient, plus methodique.",

        "Le rideau de fer n'est pas tombe. Il s'est etendu. "
        "L'Europe, l'Asie, l'Amerique latine... "
        "Le monde libre a retreci comme peau de chagrin."
    ],
    "domination": [
        "Le monde libre respire. L'etau s'est desserre. "
        "De Berlin a Saigon, les peuples choisissent la democratie. "
        "Vous avez gagne la Guerre Froide sans declencher la guerre chaude.",
    ],
    "survival": [
        "1991. Le mur est tombe. L'URSS s'effondre. "
        "Vous avez survecu. Pas de triomphe eclatant, mais la paix. "
        "C'est peut-etre la seule vraie victoire possible.",
    ],
    "adversary_collapse": [
        "L'empire sovietique s'est effondre de l'interieur. "
        "Pressions economiques, course aux armements, dissidence... "
        "Vous n'avez pas eu a tirer. Ils se sont defaits seuls.",
    ],
}


# =============================================================================
# LEADER DIALOGUES FOR DEBRIEF
# =============================================================================

DEBRIEF_DIALOGUES = {
    "apocalypse": {
        "USSR": LeaderDialogue(
            speaker="Nikita Khrouchtchev",
            title="Premier Secretaire du PCUS",
            tone="bitter",
            message="Vous pensiez que nous bluffions. Vous aviez tort.",
            country="USSR",
        ),
        "USA": LeaderDialogue(
            speaker="Robert McNamara",
            title="Secretaire a la Defense",
            tone="devastated",
            message="Nous etions convaincus d'avoir raison. C'est peut-etre ca, le pire.",
            country="USA",
        ),
    },
    "coup_etat": {
        "military": LeaderDialogue(
            speaker="General Curtis LeMay",
            title="Chef d'Etat-Major de l'Air",
            tone="cold",
            message="C'etait necessaire. L'ordre doit etre preserve.",
            country="USA",
        ),
        "congress": LeaderDialogue(
            speaker="Senateur Fulbright",
            title="President de la Commission des Affaires Etrangeres",
            tone="resigned",
            message="Le President nous a forces la main. Nous n'avions plus le choix.",
            country="USA",
        ),
    },
    "defeat_honorable": {
        "USSR": LeaderDialogue(
            speaker="Le Secretaire General",
            title="PCUS",
            tone="triumphant",
            message="L'Histoire a tranche. Le socialisme a vaincu.",
            country="USSR",
        ),
    },
    "domination": {
        "USA": LeaderDialogue(
            speaker="Le President",
            title="Etats-Unis d'Amerique",
            tone="solemn",
            message="La liberte a prevalu. Mais a quel prix?",
            country="USA",
        ),
    },
}


# =============================================================================
# PRESS HEADLINES FOR DEBRIEF
# =============================================================================

DEBRIEF_HEADLINES = {
    "apocalypse": [
        PressHeadline(
            source="BBC World Service", source_id="bbc", headline="THE END",
            excerpt="La derniere emission. Adieu.", sentiment="negative",
            bias="neutral", country="GBR", credibility="high"
        ),
        PressHeadline(
            source="Pravda", source_id="pravda",
            headline="L'agression imperialiste a detruit le monde",
            excerpt="Les dirigeants capitalistes porteront cette responsabilite pour l'eternite.",
            sentiment="negative", bias="pro_east", country="USSR", credibility="medium"
        ),
    ],
    "coup_etat": [
        PressHeadline(
            source="The Washington Post", source_id="wapo",
            headline="Putsch a la Maison Blanche",
            excerpt="Le Pentagone prend le controle. Etat d'urgence declare.",
            sentiment="negative", bias="neutral", country="USA", credibility="high"
        ),
        PressHeadline(
            source="Le Monde", source_id="le_monde",
            headline="L'Amerique bascule dans l'autoritarisme",
            excerpt="La plus vieille democratie du monde succombe a ses demons.",
            sentiment="negative", bias="neutral", country="FRA", credibility="high"
        ),
    ],
    "defeat_honorable": [
        PressHeadline(
            source="Pravda", source_id="pravda",
            headline="Victoire finale du socialisme",
            excerpt="Le XXe siecle sera celui de Marx et Lenine.",
            sentiment="positive", bias="pro_east", country="USSR", credibility="medium"
        ),
    ],
    "domination": [
        PressHeadline(
            source="The New York Times", source_id="nyt",
            headline="A New Era of Freedom",
            excerpt="Democracy prevails as the Iron Curtain falls.",
            sentiment="positive", bias="pro_west", country="USA", credibility="high"
        ),
    ],
}


# =============================================================================
# CAUSE ANALYSIS
# =============================================================================

def analyze_defeat_causes(
    end_reason: str,
    world_state: Any,  # NarrativeWorldState
    silence_state: Any,  # SilenceState
    turn_history: List[Dict] = None,
) -> List[DebriefCause]:
    """
    Analyse les decisions cles qui ont mene a la defaite.

    Extrait 3-5 causes principales basees sur:
    - L'historique du silence (tours sans action)
    - Les zones perdues
    - Les escalades militaires
    - Les dossiers ignores
    - La chute de stabilite

    Args:
        end_reason: Type de defaite (apocalypse, coup_etat, etc.)
        world_state: Etat final du monde
        silence_state: Etat du silence (historique d'inaction)
        turn_history: Historique des tours (optionnel)

    Returns:
        Liste de 3-5 DebriefCause
    """
    causes: List[DebriefCause] = []
    turn_history = turn_history or []

    # Analyse selon le type de defaite
    if end_reason == "apocalypse":
        causes.extend(_analyze_apocalypse_causes(world_state, turn_history))
    elif end_reason == "coup_etat":
        causes.extend(_analyze_coup_causes(world_state, silence_state, turn_history))
    elif end_reason == "defeat_honorable":
        causes.extend(_analyze_defeat_causes_influence(world_state, turn_history))

    # Toujours analyser le silence si pertinent
    silence_causes = _analyze_silence_causes(silence_state, end_reason)
    causes.extend(silence_causes)

    # Limiter a 5 causes max, triees par severite
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    causes.sort(key=lambda c: severity_order.get(c.severity, 2))

    return causes[:5]


def _analyze_apocalypse_causes(
    world_state: Any,
    turn_history: List[Dict],
) -> List[DebriefCause]:
    """Analyse les causes d'une apocalypse (DEFCON 1)"""
    causes = []
    current_turn = getattr(world_state, 'turn', 1)

    # Chercher les escalades dans l'historique
    escalation_count = 0
    last_escalation_turn = 0

    for entry in turn_history:
        actions = entry.get("actions", [])
        for action in actions:
            action_type = action.get("type", "")
            if any(t in action_type.upper() for t in ["MIL", "BLOCKADE", "DEMO", "THREAT"]):
                escalation_count += 1
                last_escalation_turn = entry.get("turn", current_turn)

    if escalation_count >= 3:
        causes.append(DebriefCause(
            turn=last_escalation_turn,
            category=CauseCategory.ESCALATION,
            narrative_fr="L'escalade militaire repetee a ferme les portes diplomatiques.",
            contributed_to="apocalypse",
            severity="critical",
        ))

    # Verifier les zones en crise
    for zone_id, zone in getattr(world_state, 'zones', {}).items():
        if getattr(zone, 'has_crisis', False):
            crisis_type = getattr(zone, 'crisis_type', 'unknown')
            zone_fr = ZONE_NAMES_FR.get(zone_id, zone_id)
            causes.append(DebriefCause(
                turn=current_turn,
                category=CauseCategory.PROVOCATION,
                zone=zone_id,
                narrative_fr=f"La crise en {zone_fr} n'a jamais trouve d'issue.",
                contributed_to="apocalypse",
                severity="high",
            ))
            break  # Une seule cause de zone

    # Defcon bas = cause
    defcon = getattr(world_state, 'defcon', 3)
    if defcon <= 2:
        causes.append(DebriefCause(
            turn=current_turn - 1,
            category=CauseCategory.MISCALCULATION,
            narrative_fr="Le dernier ultimatum n'a laisse aucune issue.",
            contributed_to="apocalypse",
            severity="critical",
        ))

    return causes


def _analyze_coup_causes(
    world_state: Any,
    silence_state: Any,
    turn_history: List[Dict],
) -> List[DebriefCause]:
    """Analyse les causes d'un coup d'etat (stabilite < 20)"""
    causes = []
    current_turn = getattr(world_state, 'turn', 1)

    # Le silence est la cause principale d'un coup
    total_empty = getattr(silence_state, 'total_empty_jumps', 0)
    if total_empty >= 3:
        causes.append(DebriefCause(
            turn=current_turn - total_empty,
            category=CauseCategory.SILENCE,
            actor="Pentagon",
            narrative_fr=f"Votre silence pendant {total_empty} tours a laisse le Pentagon agir seul.",
            contributed_to="coup_etat",
            severity="critical",
        ))

    # Dossiers ignores
    ignored = getattr(silence_state, 'ignored_dossiers', [])
    if len(ignored) >= 3:
        causes.append(DebriefCause(
            turn=current_turn - 2,
            category=CauseCategory.OMISSION,
            narrative_fr=f"Les dossiers urgents sont restes sans reponse. {len(ignored)} decisions en attente.",
            contributed_to="coup_etat",
            severity="high",
        ))

    # Stabilite basse
    player = getattr(world_state, 'player', None)
    if player:
        stability = getattr(player, 'domestic_stability', 50)
        if stability < 30:
            causes.append(DebriefCause(
                turn=current_turn,
                category=CauseCategory.INSTABILITY,
                actor="Congress",
                narrative_fr="Le Congres a perdu confiance. Votre autorite s'est effritee.",
                contributed_to="coup_etat",
                severity="high",
            ))

    return causes


def _analyze_defeat_causes_influence(
    world_state: Any,
    turn_history: List[Dict],
) -> List[DebriefCause]:
    """Analyse les causes d'une defaite par influence"""
    causes = []
    current_turn = getattr(world_state, 'turn', 1)

    # Zones perdues
    zones = getattr(world_state, 'zones', {})
    lost_zones = []
    for zone_id, zone in zones.items():
        influence_us = getattr(zone, 'influence_us', 50)
        influence_ussr = getattr(zone, 'influence_ussr', 50)
        if influence_ussr > influence_us + 20:
            lost_zones.append(zone_id)

    if lost_zones:
        first_lost = lost_zones[0]
        zone_fr = ZONE_NAMES_FR.get(first_lost, first_lost)
        causes.append(DebriefCause(
            turn=current_turn // 2,  # Estimation mi-partie
            category=CauseCategory.OMISSION,
            zone=first_lost,
            narrative_fr=f"{zone_fr} a bascule dans l'orbite sovietique.",
            contributed_to="defeat_honorable",
            severity="high",
        ))

    if len(lost_zones) >= 3:
        causes.append(DebriefCause(
            turn=current_turn,
            category=CauseCategory.ISOLATION,
            narrative_fr=f"{len(lost_zones)} zones strategiques perdues. L'influence s'est erodee.",
            contributed_to="defeat_honorable",
            severity="critical",
        ))

    return causes


def _analyze_silence_causes(
    silence_state: Any,
    end_reason: str,
) -> List[DebriefCause]:
    """Analyse les causes liees au silence"""
    causes = []

    if not silence_state:
        return causes

    streak = getattr(silence_state, 'silence_streak', 0)
    total_empty = getattr(silence_state, 'total_empty_jumps', 0)
    pressure = getattr(silence_state, 'pressure_cards', 0)

    # Streak consecutive important
    if streak >= 3:
        causes.append(DebriefCause(
            turn=0,  # Sera calcule
            category=CauseCategory.SILENCE,
            narrative_fr=f"{streak} tours consecutifs sans directives. L'appareil d'Etat a improvise.",
            contributed_to=end_reason,
            severity="high" if streak >= 4 else "medium",
        ))

    # Pression accumulee
    if pressure >= 5 and end_reason == "coup_etat":
        causes.append(DebriefCause(
            turn=0,
            category=CauseCategory.INSTABILITY,
            narrative_fr="La pression s'est accumulee. Quand elle a explose, il etait trop tard.",
            contributed_to=end_reason,
            severity="high",
        ))

    return causes


# =============================================================================
# DEBRIEF COMPOSITION
# =============================================================================

def compose_debrief(
    end_reason: str,
    victory: bool,
    world_state: Any,
    silence_state: Any = None,
    turn_history: List[Dict] = None,
    ai_errors: List[AIStrategicError] = None,
) -> GameDebrief:
    """
    Compose le debrief narratif complet.

    Args:
        end_reason: Type de fin (apocalypse, coup_etat, etc.)
        victory: True si c'est une victoire
        world_state: Etat final du monde
        silence_state: Etat du silence
        turn_history: Historique des tours
        ai_errors: Erreurs strategiques de l'IA adversaire

    Returns:
        GameDebrief pret a afficher
    """
    import random

    # 1. Titre dramatique
    title = DEFEAT_TITLES.get(end_reason, "Fin de partie")

    # 2. Recit principal
    narratives = DEFEAT_NARRATIVES.get(end_reason, ["La partie est terminee."])
    narrative = random.choice(narratives)

    # 3. Analyser les causes
    causes = []
    if not victory and silence_state:
        causes = analyze_defeat_causes(
            end_reason=end_reason,
            world_state=world_state,
            silence_state=silence_state,
            turn_history=turn_history,
        )

    # 4. Dialogue de leader
    leader_dialogue = None
    dialogues = DEBRIEF_DIALOGUES.get(end_reason, {})
    if dialogues:
        # Choisir un dialogue pertinent
        if end_reason == "coup_etat":
            leader_dialogue = dialogues.get("military")
        else:
            leader_dialogue = dialogues.get("USSR") or dialogues.get("USA")

    # 5. Headlines presse
    press_headlines = DEBRIEF_HEADLINES.get(end_reason, [])

    # 6. Resume de l'etat final (narrativise)
    final_summary = _compose_final_summary(world_state, end_reason, victory)

    debrief = GameDebrief(
        end_reason=end_reason,
        victory=victory,
        title_fr=title,
        narrative_fr=narrative,
        causes=causes,
        leader_dialogue=leader_dialogue,
        press_headlines=press_headlines,
        final_state_summary=final_summary,
        ai_errors=ai_errors or [],
    )

    logger.info(f"Debrief composed: {end_reason}, {len(causes)} causes, {len(ai_errors or [])} AI errors")
    return debrief


def _compose_final_summary(
    world_state: Any,
    end_reason: str,
    victory: bool,
) -> Dict[str, str]:
    """
    Resume narratif de l'etat final (sans chiffres!).

    Au lieu de "DEFCON: 2", on dit "Le monde au bord du gouffre".
    """
    summary = {}

    # DEFCON narrativise
    defcon = getattr(world_state, 'defcon', 3)
    defcon_phrases = {
        1: "L'apocalypse nucleaire",
        2: "Le monde au bord du gouffre",
        3: "Une tension insupportable",
        4: "Un calme precaire",
        5: "Une paix fragile",
    }
    summary["situation_mondiale"] = defcon_phrases.get(defcon, "Incertaine")

    # Stabilite narrativisee
    player = getattr(world_state, 'player', None)
    if player:
        stability = getattr(player, 'domestic_stability', 50)
        if stability < 20:
            summary["situation_interieure"] = "Le gouvernement a perdu le controle"
        elif stability < 40:
            summary["situation_interieure"] = "L'autorite vacille"
        elif stability < 60:
            summary["situation_interieure"] = "Des tensions persistantes"
        else:
            summary["situation_interieure"] = "Le pays reste uni"

        # Reputation
        reputation = getattr(player, 'international_reputation', 50)
        if reputation < 30:
            summary["reputation"] = "Isole sur la scene internationale"
        elif reputation < 50:
            summary["reputation"] = "Des allies qui doutent"
        elif reputation < 70:
            summary["reputation"] = "Respecte mais conteste"
        else:
            summary["reputation"] = "Leader du monde libre"

    # Influence globale narrativisee
    zones = getattr(world_state, 'zones', {})
    if zones:
        us_total = sum(getattr(z, 'influence_us', 0) for z in zones.values())
        ussr_total = sum(getattr(z, 'influence_ussr', 0) for z in zones.values())
        avg_us = us_total / len(zones)
        avg_ussr = ussr_total / len(zones)

        if avg_us > avg_ussr + 15:
            summary["equilibre_mondial"] = "L'Occident domine"
        elif avg_ussr > avg_us + 15:
            summary["equilibre_mondial"] = "Le bloc de l'Est progresse"
        else:
            summary["equilibre_mondial"] = "Un monde divise"

    return summary


# =============================================================================
# AI ERROR EXTRACTION
# =============================================================================

def extract_ai_errors_for_debrief(
    adversary_ai: Any,
    current_turn: int,
) -> List[AIStrategicError]:
    """
    Extrait les erreurs strategiques de l'IA adversaire pour le debrief.

    Transforme les erreurs internes en erreurs narratives lisibles.

    Args:
        adversary_ai: Instance de AdversaryAI avec perception engine
        current_turn: Tour actuel (pour contexte)

    Returns:
        Liste d'erreurs strategiques narrativisees
    """
    errors: List[AIStrategicError] = []

    if not adversary_ai:
        return errors

    # Recuperer les erreurs du perception engine
    raw_errors = []
    if hasattr(adversary_ai, 'get_ai_errors'):
        raw_errors = adversary_ai.get_ai_errors()
    elif hasattr(adversary_ai, 'perception_engine'):
        pe = adversary_ai.perception_engine
        if hasattr(pe, 'get_errors'):
            raw_errors = pe.get_errors()
        elif hasattr(pe, 'errors'):
            raw_errors = pe.errors

    # Convertir en AIStrategicError avec narratif + score dramatique
    for raw in raw_errors:
        # Supporter dict et dataclass
        raw_dict = _error_to_dict(raw)

        error_type = raw_dict.get('error_type') or raw_dict.get('type', 'misread')
        turn = raw_dict.get('turn', current_turn)

        # Generer les textes narratifs selon le type d'erreur
        belief_fr, reality_fr, consequence_fr = _narrativize_ai_error(raw_dict)

        # Calculer le score dramatique
        drama_score = _calculate_drama_score(raw_dict, turn, current_turn)

        # Extraire la zone pour la diversite
        zone = _get_error_zone(raw_dict)

        errors.append({
            'error': AIStrategicError(
                turn=turn,
                error_type=error_type,
                belief_fr=belief_fr,
                reality_fr=reality_fr,
                consequence_fr=consequence_fr,
            ),
            'score': drama_score,
            'zone': zone,  # Pour la diversite geographique
        })

    # Trier par score dramatique (les plus dramatiques en premier)
    errors.sort(key=lambda e: e['score'], reverse=True)

    # Selectionner les 2 plus dramatiques avec DIVERSITE
    # Regle: eviter 2 erreurs du meme type si possible
    selected = _select_diverse_errors(errors, max_count=2)

    return selected


def _get_error_zone(raw_error: Dict) -> Optional[str]:
    """Extrait la zone d'une erreur (dict ou erreur deja construite)."""
    # Essayer d'abord sur l'erreur brute
    zone = raw_error.get('zone')
    if zone:
        return zone
    # Essayer sur le sujet (peut contenir une zone)
    subject = raw_error.get('subject', '')
    if subject and subject in ZONE_NAMES_FR:
        return subject
    return None


def _select_diverse_errors(
    scored_errors: List[Dict],
    max_count: int = 2,
) -> List[AIStrategicError]:
    """
    Selectionne les erreurs les plus dramatiques avec diversite.

    Diversite sur deux axes:
    1. Type d'erreur (misread_player, underestimation, etc.)
    2. Zone/front (Cuba, Berlin, Europe, etc.)

    Regle: si le top2 sont du meme type OU de la meme zone,
    remplace le second par le meilleur candidat divers (si score >= 50%).

    Args:
        scored_errors: Liste de {'error': AIStrategicError, 'score': float, 'raw': dict}
        max_count: Nombre max d'erreurs a retourner

    Returns:
        Liste d'AIStrategicError diversifiees
    """
    if len(scored_errors) == 0:
        return []

    if len(scored_errors) == 1:
        return [scored_errors[0]['error']]

    # Premier: toujours le plus dramatique
    first = scored_errors[0]
    first_type = first['error'].error_type
    first_zone = first.get('zone')  # Zone extraite lors du scoring

    # Chercher le second
    second = scored_errors[1]
    second_type = second['error'].error_type
    second_zone = second.get('zone')

    # Verifier si on a besoin de diversifier (meme type OU meme zone)
    needs_diversity = (first_type == second_type) or (
        first_zone and second_zone and first_zone == second_zone
    )

    if needs_diversity:
        # Chercher le meilleur candidat qui differe sur au moins un axe
        for candidate in scored_errors[2:]:
            cand_type = candidate['error'].error_type
            cand_zone = candidate.get('zone')

            # Le candidat doit differer sur au moins un axe
            type_differs = (cand_type != first_type)
            zone_differs = (not first_zone) or (not cand_zone) or (cand_zone != first_zone)

            if type_differs or zone_differs:
                # Verifier que le score n'est pas trop loin
                score_ratio = candidate['score'] / first['score'] if first['score'] > 0 else 0
                if score_ratio >= 0.5:  # Au moins 50% du score du premier
                    second = candidate
                    break

    result = [first['error']]
    if max_count >= 2:
        result.append(second['error'])

    return result


def _error_to_dict(raw: Any) -> Dict:
    """Convertit une erreur (dict ou dataclass) en dict."""
    if isinstance(raw, dict):
        return raw
    # Dataclass - utiliser asdict ou extraire manuellement
    if hasattr(raw, '__dataclass_fields__'):
        return {
            'turn': getattr(raw, 'turn', 0),
            'error_type': getattr(raw, 'error_type', 'misread'),
            'subject': getattr(raw, 'subject', ''),
            'zone': getattr(raw, 'zone', None),
            'belief': getattr(raw, 'belief', ''),
            'reality': getattr(raw, 'reality', ''),
            'consequence': getattr(raw, 'consequence', ''),
            'consequence_fr': getattr(raw, 'consequence_fr', ''),
            'action_taken': getattr(raw, 'action_taken', None),
            'result': getattr(raw, 'result', None),
            'escalation_delta': getattr(raw, 'escalation_delta', 0),
            'factions': getattr(raw, 'factions', None),
        }
    # Objet generique
    return {k: getattr(raw, k, None) for k in dir(raw) if not k.startswith('_')}


def _calculate_drama_score(raw_error: Dict, turn: int, current_turn: int) -> float:
    """
    Calcule un score dramatique pour prioriser les erreurs les plus impactantes.

    Criteres:
    - Type d'erreur (misread_player > faction_conflict > autres)
    - Impact (a mene a escalade, crise, perte?)
    - Recence (bonus leger pour fin de partie)
    """
    score = 0.0
    error_type = raw_error.get('error_type') or raw_error.get('type', 'misread')

    # 1. Poids par type d'erreur (0-40 points)
    type_weights = {
        'misread_player': 40,      # Le plus dramatique: ils vous ont mal lu
        'faction_conflict': 35,    # Politique interne = tres narratif
        'underestimation': 30,     # Ils vous ont sous-estime
        'overestimation': 25,      # Ils ont surestime leurs chances
        'stale_intel': 20,         # Renseignements obsoletes
    }
    score += type_weights.get(error_type, 15)

    # 2. Impact (0-30 points) - base sur les consequences enregistrees
    consequence = raw_error.get('consequence', '')
    if 'escalade' in consequence.lower() or 'escalation' in consequence.lower():
        score += 30
    elif 'crise' in consequence.lower() or 'crisis' in consequence.lower():
        score += 25
    elif 'aggressive' in consequence.lower() or 'agressif' in consequence.lower():
        score += 20
    elif 'tension' in consequence.lower():
        score += 15

    # 3. Recence (0-20 points) - bonus leger pour les erreurs recentes
    if current_turn > 0:
        recency_ratio = turn / current_turn
        score += recency_ratio * 20

    # 4. Bonus si l'erreur a un sujet specifique (zone ou joueur)
    if raw_error.get('subject') or raw_error.get('zone'):
        score += 10

    return score


def _narrativize_ai_error(raw_error: Dict) -> tuple:
    """
    Transforme une erreur brute en textes narratifs avec ancrage factuel.

    Gere deux formats d'erreur:
    1. Format perception engine: {type, zone, belief: dict, reality: dict}
    2. Format adversary_ai: {error_type, subject, belief, reality, consequence_fr}

    ANCRAGE FACTUEL: Les consequences doivent etre basees sur des faits
    enregistres dans l'erreur (action_taken, result, escalation_delta, etc.)

    Returns:
        (belief_fr, reality_fr, consequence_fr)
    """
    # Detecter le format et normaliser
    error_type = raw_error.get('error_type') or raw_error.get('type', 'misread')
    zone = raw_error.get('zone') or raw_error.get('subject')
    turn = raw_error.get('turn', 0)

    # Donnees factuelles pour ancrage (si disponibles)
    action_taken = raw_error.get('action_taken', '')
    escalation_delta = raw_error.get('escalation_delta', 0)
    result = raw_error.get('result', '')

    # Si consequence_fr est deja fourni avec ancrage, l'utiliser directement
    if raw_error.get('consequence_fr') and raw_error.get('factual_anchor'):
        belief_text = raw_error.get('belief', '')
        consequence_text = raw_error.get('consequence_fr', '')

        zone_fr = ZONE_NAMES_FR.get(zone, zone) if zone else None

        if belief_text and isinstance(belief_text, str):
            belief_fr = belief_text
        elif zone_fr:
            belief_fr = f"Le Kremlin avait une lecture erronee de {zone_fr}."
        else:
            belief_fr = "Moscou a fait une erreur d'appreciation."

        return belief_fr, "", consequence_text

    # Format legacy - generer le narratif avec ancrage factuel
    belief = raw_error.get('belief', {})
    reality = raw_error.get('reality', {})
    zone_fr = ZONE_NAMES_FR.get(zone, zone) if zone else None

    # Templates selon le type d'erreur (ton "Historien" / documentaire)
    # NOTE: Chaque erreur doit avoir une CONTREPARTIE ancree dans les faits
    # Format: "Le Kremlin croyait..." plutot que "Moscou a cru..."

    if error_type == 'overestimation':
        if zone_fr:
            belief_fr = f"Le Kremlin croyait {zone_fr} prete a basculer. Elle s'est montree plus solide que prevu."
            # Ancrage factuel: consequence basee sur l'action prise
            if action_taken:
                consequence_fr = f"Leur {_action_to_fr(action_taken)} a echoue, les rendant plus agressifs."
            elif escalation_delta > 0:
                consequence_fr = "Leur echec a provoque une escalade compensatoire."
            else:
                consequence_fr = "Leur echec les a rendus plus agressifs ailleurs."
        else:
            belief_fr = "Le Kremlin surestimait ses chances. Le terrain lui a resiste."
            consequence_fr = "Cette humiliation a pousse les factions dures a prendre le dessus."

    elif error_type == 'underestimation':
        if zone_fr:
            belief_fr = f"Le KGB considerait {zone_fr} comme acquise. Elle ne l'etait pas."
            if turn > 0:
                consequence_fr = f"Tour {turn}: leur reaction tardive a fait monter les encheres."
            else:
                consequence_fr = "Leur reaction tardive a fait monter les encheres."
        else:
            belief_fr = "Khrouchtchev sous-estimait votre determination."
            if action_taken:
                consequence_fr = f"Sa {_action_to_fr(action_taken)} ratee l'a pousse a escalader."
            else:
                consequence_fr = "Sa provocation ratee l'a pousse a escalader."

    elif error_type == 'misread_player':
        resolve = belief.get('resolve', 'unknown') if isinstance(belief, dict) else 'unknown'
        if resolve == 'weak':
            belief_fr = "Le Kremlin vous croyait paralyse. Vous ne l'etiez pas."
            if result == 'failed':
                consequence_fr = "Leur offensive a ete repoussee, declenchant une crise plus grave."
            else:
                consequence_fr = "Leur offensive frontale a declenche une crise plus grave."
        elif resolve == 'aggressive':
            belief_fr = "Le Kremlin s'attendait a une frappe imminente. Vous cherchiez la paix."
            consequence_fr = "Leur posture defensive a verrouille toute negociation."
        else:
            belief_fr = "Votre strategie restait illisible pour le Politburo."
            if escalation_delta > 0:
                consequence_fr = f"Dans le doute, ils ont choisi l'escalade (tension +{escalation_delta})."
            else:
                consequence_fr = "Dans le doute, ils ont opte pour l'escalade."

    elif error_type == 'faction_conflict':
        # Ancrage: les factions ont des noms specifiques
        factions = raw_error.get('factions', ['KGB', 'Armee Rouge'])
        if isinstance(factions, list) and len(factions) >= 2:
            belief_fr = f"{factions[0]} et {factions[1]} se neutralisaient mutuellement."
        else:
            belief_fr = "Le KGB et l'Armee Rouge se neutralisaient mutuellement."
        consequence_fr = "Leur compromis bancal a rendu l'action sovietique incoherente - mais imprevisible."

    elif error_type == 'stale_intel':
        if turn > 0:
            belief_fr = f"Les renseignements du KGB dataient du tour {turn - 1}. Le monde avait change."
        else:
            belief_fr = "Les renseignements du KGB etaient obsoletes."
        consequence_fr = "Leur decision, basee sur un monde revolu, a precipite les evenements."

    else:
        # Erreur generique
        belief_fr = "Le Kremlin lisait mal la situation."
        consequence_fr = "Cette erreur a eu des consequences imprevues des deux cotes."

    return belief_fr, "", consequence_fr


def _action_to_fr(action: str) -> str:
    """Convertit un type d'action en francais narratif."""
    action_translations = {
        'destabilize': 'tentative de destabilisation',
        'military_demo': 'demonstration militaire',
        'propaganda': 'campagne de propagande',
        'diplomatic_pressure': 'pression diplomatique',
        'covert_op': 'operation secrete',
        'expand_influence': 'tentative d\'expansion',
        'support_faction': 'soutien factionnel',
    }
    return action_translations.get(action, 'initiative')


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def generate_game_debrief(
    world_state: Any,
    silence_state: Any = None,
    turn_history: List[Dict] = None,
    adversary_ai: Any = None,
) -> Dict[str, Any]:
    """
    Fonction de commodite pour generer un debrief.

    Retourne un dict pret a etre envoye au frontend.

    Args:
        world_state: Etat final du monde
        silence_state: Etat du silence
        turn_history: Historique des tours
        adversary_ai: Instance de l'IA adversaire (optionnel)
    """
    end_reason = getattr(world_state, 'end_reason', 'unknown')
    victory = getattr(world_state, 'victory', False)
    current_turn = getattr(world_state, 'turn', 1)

    # Extraire les erreurs de l'IA si disponible
    ai_errors = []
    if adversary_ai:
        ai_errors = extract_ai_errors_for_debrief(adversary_ai, current_turn)

    debrief = compose_debrief(
        end_reason=end_reason,
        victory=victory,
        world_state=world_state,
        silence_state=silence_state,
        turn_history=turn_history,
        ai_errors=ai_errors,
    )

    return debrief.to_dict()
