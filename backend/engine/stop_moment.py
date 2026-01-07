"""
Stop Moment - "Moment de Verite" Generator

Transforme un arret technique (PauseReason) en moment memorable.
Comme le "You Died" de Dark Souls, mais en Guerre Froide.

Le joueur ne voit jamais "DEFCON_CHANGED" - il voit:
"Les silos s'ouvrent."
"L'alerte n'est plus un exercice."

PHILOSOPHIE:
Le joueur ne choisit pas quand le monde s'arrete.
Il decouvre quand il n'a plus le choix.
"""
import random
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StopTone(str, Enum):
    """Ton dramatique du moment"""
    DREAD = "dread"           # Peur sourde
    SHOCK = "shock"           # Surprise violente
    GRAVITY = "gravity"       # Poids du moment
    RESIGNATION = "resignation"  # Fatalite
    REVELATION = "revelation"    # Verite qui eclate
    TURNING_POINT = "turning_point"  # Bascule


class DramaticAngle(str, Enum):
    """Angle dramaturgique du moment"""
    IRREVERSIBILITY = "irreversibility"  # Point de non-retour
    LOSS_OF_CONTROL = "loss_of_control"  # Le monde echappe
    REVELATION = "revelation"             # Verite cachee
    MORAL_SHIFT = "moral_shift"           # Bascule morale


@dataclass
class StopMoment:
    """Un moment de verite - l'arret devient memorable"""
    id: str
    title: str
    subtitle: str
    tone: StopTone
    angle: DramaticAngle
    tag: str = "moment_of_truth"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "tone": self.tone.value,
            "angle": self.angle.value,
            "tag": self.tag,
        }


# =============================================================================
# POOL DE PHRASES PAR RAISON D'ARRET
# =============================================================================
# 6-12 phrases par raison pour la variabilite
# Chaque phrase a un tone et un angle specifique

STOP_MOMENT_POOL: Dict[str, list] = {
    # DEFCON CHANGE - L'escalade nucleaire
    "defcon_changed": [
        {
            "title": "Les silos s'ouvrent.",
            "subtitle": "L'alerte monte. Les etats-majors basculent en procedure reelle.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Les cles tournent.",
            "subtitle": "Dans les bunkers, les officiers verifient leurs codes.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "L'alerte n'est plus un exercice.",
            "subtitle": "Le President a ete reveille. Les options se reduisent.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Le compte a rebours commence.",
            "subtitle": "Quelque part, un radar a detecte quelque chose.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "Les sous-marins plongent.",
            "subtitle": "La triade nucleaire se met en position.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Le monde bascule.",
            "subtitle": "Ce qui etait impensable devient imminent.",
            "tone": StopTone.TURNING_POINT,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
    ],

    # WAR DECLARED - La guerre eclate
    "war_declared": [
        {
            "title": "Le premier coup de feu a ete tire.",
            "subtitle": "Il n'y aura pas de retour en arriere.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Les frontieres s'embrasent.",
            "subtitle": "Les armees sont en mouvement.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "La guerre a un nom maintenant.",
            "subtitle": "Les historiens dateront ce jour.",
            "tone": StopTone.REVELATION,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "Les declarations sont parties.",
            "subtitle": "Les ambassades ferment. Les civils fuient.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Le sang a coule.",
            "subtitle": "La diplomatie a echoue.",
            "tone": StopTone.RESIGNATION,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "L'ultimatum a expire.",
            "subtitle": "Les mots ne servent plus a rien.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
    ],

    # CRISIS STARTED - Une crise eclate
    "crisis_started": [
        {
            "title": "Le telephone rouge sonne.",
            "subtitle": "Quelque chose vient de se passer.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "La crise trouve enfin un nom.",
            "subtitle": "Ce qui couvait depuis des semaines vient d'eclater.",
            "tone": StopTone.REVELATION,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "Les chancelleries s'eteignent.",
            "subtitle": "Plus personne ne repond. Le silence est lourd.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "Le monde decouvre ce que vous saviez.",
            "subtitle": "Les journaux du matin vont changer d'ici.",
            "tone": StopTone.REVELATION,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "L'incident devient la crise.",
            "subtitle": "Ce qui etait local devient global.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "Les masques tombent.",
            "subtitle": "Les veritables intentions se revelent.",
            "tone": StopTone.REVELATION,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
    ],

    # CRISIS ESCALATED - Une crise s'intensifie
    "crisis_escalated": [
        {
            "title": "La situation echappe a tout le monde.",
            "subtitle": "Meme ceux qui ont commence ne savent plus comment arreter.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "Le point de non-retour.",
            "subtitle": "Ce qui suit ne peut plus etre annule.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Les moderees ont perdu.",
            "subtitle": "Les faucons tiennent les renes maintenant.",
            "tone": StopTone.RESIGNATION,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "L'escalade continue.",
            "subtitle": "Chaque camp mise plus haut. Personne ne recule.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "Les lignes rouges sont franchies.",
            "subtitle": "Ce qui etait inacceptable est devenu realite.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
    ],

    # NUCLEAR EVENT - Evenement nucleaire
    "nuclear_event": [
        {
            "title": "L'atome a parle.",
            "subtitle": "Un champignon s'eleve. Le monde ne sera plus jamais le meme.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Le soleil s'est leve deux fois.",
            "subtitle": "Quelque part, une ville n'existe plus.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "L'impensable s'est produit.",
            "subtitle": "Toutes les regles viennent de changer.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Le genie est sorti de la bouteille.",
            "subtitle": "On ne peut plus faire semblant.",
            "tone": StopTone.REVELATION,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "L'horloge de l'apocalypse avance.",
            "subtitle": "Les scientifiques ajustent les aiguilles.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
    ],

    # PLAYER ATTACKED - Le joueur est attaque
    "player_attacked": [
        {
            "title": "Ils ont frappe en premier.",
            "subtitle": "Votre pays est sous attaque.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "L'agression est confirmee.",
            "subtitle": "Les rapports arrivent. C'est bien reel.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Votre tour est venu.",
            "subtitle": "Vous n'etes plus spectateur.",
            "tone": StopTone.DREAD,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "La provocation a reussi.",
            "subtitle": "Vous devez reagir. Mais comment?",
            "tone": StopTone.TURNING_POINT,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
    ],

    # PLAYER MENTIONED - Le joueur est mentionne dans un evenement
    "player_mentioned": [
        {
            "title": "Votre nom est prononce.",
            "subtitle": "Le monde vous regarde. Qu'allez-vous faire?",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "L'attention se tourne vers vous.",
            "subtitle": "Les cameras, les micros, les telescopes - tout vous vise.",
            "tone": StopTone.TURNING_POINT,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "On attend votre reponse.",
            "subtitle": "Le silence n'est pas une option.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
    ],

    # IMPORTANT EVENT - Evenement majeur generique
    "important_event": [
        {
            "title": "L'Histoire vient de s'ecrire.",
            "subtitle": "Ce moment restera dans les livres.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "Quelque chose a change.",
            "subtitle": "Le monde d'avant n'existe plus.",
            "tone": StopTone.REVELATION,
            "angle": DramaticAngle.REVELATION,
        },
        {
            "title": "Un tournant.",
            "subtitle": "Les equilibres viennent de basculer.",
            "tone": StopTone.TURNING_POINT,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "L'inattendu frappe.",
            "subtitle": "Meme les analystes n'avaient pas prevu ca.",
            "tone": StopTone.SHOCK,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
    ],

    # GOAL CONFLICT - Conflit d'objectifs
    "goal_conflict": [
        {
            "title": "Vos interets s'affrontent.",
            "subtitle": "Vous ne pouvez pas tout avoir.",
            "tone": StopTone.TURNING_POINT,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "Le dilemme se pose.",
            "subtitle": "Chaque choix a un cout.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "Les allies divergent.",
            "subtitle": "Ce qui vous unissait ne suffit plus.",
            "tone": StopTone.RESIGNATION,
            "angle": DramaticAngle.REVELATION,
        },
    ],

    # WAR ENDED - Une guerre se termine
    "war_ended": [
        {
            "title": "Le silence apres les armes.",
            "subtitle": "Les canons se taisent. Pour combien de temps?",
            "tone": StopTone.RESIGNATION,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
        {
            "title": "La paix a un prix.",
            "subtitle": "Les comptes ne sont pas regles. Ils sont reportes.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.MORAL_SHIFT,
        },
        {
            "title": "Fin des hostilites.",
            "subtitle": "Mais pas des rancœurs.",
            "tone": StopTone.RESIGNATION,
            "angle": DramaticAngle.REVELATION,
        },
    ],

    # MAX DAYS REACHED - Temps ecoule
    "max_days_reached": [
        {
            "title": "Le temps a passe.",
            "subtitle": "L'Histoire continue, avec ou sans vous.",
            "tone": StopTone.RESIGNATION,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
        {
            "title": "Une ere s'acheve.",
            "subtitle": "Le monde a change pendant que vous regardiez.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.IRREVERSIBILITY,
        },
    ],

    # MANUAL PAUSE - Pause manuelle (rare)
    "manual_pause": [
        {
            "title": "Pause.",
            "subtitle": "Le monde attend.",
            "tone": StopTone.GRAVITY,
            "angle": DramaticAngle.LOSS_OF_CONTROL,
        },
    ],
}


# =============================================================================
# GENERATEUR DE STOP MOMENT
# =============================================================================

def generate_stop_moment(
    pause_reason: str,
    context: Optional[Dict] = None,
    event_id: Optional[str] = None,
) -> StopMoment:
    """
    Genere un "Moment de Verite" a partir d'une raison d'arret.

    Args:
        pause_reason: La raison technique (ex: "defcon_changed")
        context: Contexte additionnel (defcon level, zone, etc.)
        event_id: ID de l'evenement declencheur

    Returns:
        StopMoment pret a afficher
    """
    # Normaliser la raison (enum -> string)
    reason_key = pause_reason.lower() if isinstance(pause_reason, str) else pause_reason.value.lower()

    # Trouver le pool de phrases
    pool = STOP_MOMENT_POOL.get(reason_key, STOP_MOMENT_POOL["important_event"])

    # Choisir une phrase aleatoirement
    phrase = random.choice(pool)

    # Generer un ID unique
    import time
    moment_id = event_id or f"stop_{reason_key}_{int(time.time())}"

    return StopMoment(
        id=moment_id,
        title=phrase["title"],
        subtitle=phrase["subtitle"],
        tone=phrase["tone"],
        angle=phrase["angle"],
    )


def get_stop_moment_for_reason(pause_reason: str, context: Optional[Dict] = None) -> Dict:
    """
    Helper rapide pour obtenir un stop_moment en dict.

    Usage:
        stop_moment = get_stop_moment_for_reason("defcon_changed")
        response["stop_moment"] = stop_moment
    """
    moment = generate_stop_moment(pause_reason, context)
    return moment.to_dict()
