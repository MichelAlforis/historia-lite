"""
Council Suggestions - "Conseil des urgences"

Detecte les dossiers urgents et propose des suggestions AVANT le jump.
Le joueur prepare ses decisions pendant que le monde prepare ses consequences.

PHILOSOPHIE:
- Le Conseil ne dit pas "faites ceci" mais "voici ce qui brule"
- Chaque dossier = 2-3 suggestions (pas d'action parfaite)
- Cliquer une suggestion = pre-remplir la queue (pas executer)
- Le joueur peut ignorer consciemment

Types de dossiers:
1. CRISES ACTIVES - Zones en crise (stability < 30, has_crisis)
2. OPPORTUNITES - Zones contestees proches du basculement
3. PRESSIONS INTERNES - Domestic stability basse, capital critique
4. SOMMETS - Possibilites diplomatiques (adversary en detente)
"""
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DossierType(str, Enum):
    """Type de dossier urgent"""
    CRISIS = "crisis"           # Crise active
    OPPORTUNITY = "opportunity" # Opportunite a saisir
    PRESSURE = "pressure"       # Pression interne
    SUMMIT = "summit"           # Possibilite diplomatique
    THREAT = "threat"           # Menace imminente


class DossierUrgency(str, Enum):
    """Niveau d'urgence"""
    CRITICAL = "critical"   # Rouge - action immediate requise
    HIGH = "high"           # Orange - deterioration rapide
    MODERATE = "moderate"   # Jaune - attention requise
    LOW = "low"             # Info - a surveiller


@dataclass
class SuggestedAction:
    """Une action suggeree par le Conseil"""
    id: str
    label: str              # Ex: "Negocier"
    description_fr: str     # Ex: "Ouvrir des canaux diplomatiques avec Cuba"

    # Pour pre-remplir la queue
    intention_type: str     # Ex: "DIPLO_NEGOTIATE"
    intention_id: str
    target_zone: Optional[str] = None
    target_actor: Optional[str] = None
    political_cost: int = 0
    risk_level: str = "low"
    predicted_effects: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "description_fr": self.description_fr,
            "intention_type": self.intention_type,
            "intention_id": self.intention_id,
            "target_zone": self.target_zone,
            "target_actor": self.target_actor,
            "political_cost": self.political_cost,
            "risk_level": self.risk_level,
            "predicted_effects": self.predicted_effects,
        }


@dataclass
class UrgentDossier:
    """Un dossier urgent presente au joueur"""
    id: str
    type: DossierType
    urgency: DossierUrgency

    title_fr: str           # Ex: "Crise a Cuba"
    summary_fr: str         # Ex: "Les missiles sovietiques menacent..."

    zone_id: Optional[str] = None
    actor_id: Optional[str] = None

    # 2-3 suggestions d'actions
    suggestions: List[SuggestedAction] = field(default_factory=list)

    # Metadata
    days_active: int = 0
    last_escalation: Optional[str] = None  # Description du dernier evenement

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "urgency": self.urgency.value,
            "title_fr": self.title_fr,
            "summary_fr": self.summary_fr,
            "zone_id": self.zone_id,
            "actor_id": self.actor_id,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "days_active": self.days_active,
            "last_escalation": self.last_escalation,
        }


def detect_urgent_dossiers(state: Any) -> List[UrgentDossier]:
    """
    Analyse l'etat du monde et detecte les dossiers urgents.

    Args:
        state: NarrativeWorldState

    Returns:
        Liste de dossiers urgents tries par urgence
    """
    dossiers = []

    # 1. CRISES ACTIVES - Zones en crise
    for zone_id, zone in state.zones.items():
        if zone.has_crisis or zone.stability < 30:
            dossier = _create_crisis_dossier(zone_id, zone, state)
            if dossier:
                dossiers.append(dossier)

    # 2. OPPORTUNITES - Zones contestees proches du basculement
    for zone_id, zone in state.zones.items():
        if _is_opportunity(zone):
            dossier = _create_opportunity_dossier(zone_id, zone, state)
            if dossier:
                dossiers.append(dossier)

    # 3. PRESSIONS INTERNES
    if state.player.domestic_stability < 50 or state.player.political_capital < 30:
        dossier = _create_internal_pressure_dossier(state)
        if dossier:
            dossiers.append(dossier)

    # 4. OPPORTUNITES DIPLOMATIQUES
    if _can_negotiate(state):
        dossier = _create_summit_dossier(state)
        if dossier:
            dossiers.append(dossier)

    # 5. MENACES IMMINENTES (DEFCON bas, tension haute)
    if state.defcon <= 2 or state.world_tension > 80:
        dossier = _create_threat_dossier(state)
        if dossier:
            dossiers.append(dossier)

    # Trier par urgence (critical > high > moderate > low)
    urgency_order = {
        DossierUrgency.CRITICAL: 0,
        DossierUrgency.HIGH: 1,
        DossierUrgency.MODERATE: 2,
        DossierUrgency.LOW: 3,
    }
    dossiers.sort(key=lambda d: urgency_order.get(d.urgency, 99))

    # Max 4 dossiers (comme les crises)
    return dossiers[:4]


def _create_crisis_dossier(zone_id: str, zone: Any, state: Any) -> Optional[UrgentDossier]:
    """Cree un dossier pour une zone en crise"""

    # Determiner l'urgence
    if zone.stability < 20 or (zone.has_crisis and zone.crisis_intensity > 70):
        urgency = DossierUrgency.CRITICAL
    elif zone.stability < 30 or zone.has_crisis:
        urgency = DossierUrgency.HIGH
    else:
        urgency = DossierUrgency.MODERATE

    # Titre et resume
    crisis_names = {
        "missiles_cuba": "Crise des missiles",
        "instability": "Instabilite regionale",
    }
    crisis_name = crisis_names.get(zone.crisis_type, "Crise") if zone.has_crisis else "Instabilite"

    dossier = UrgentDossier(
        id=f"crisis_{zone_id}",
        type=DossierType.CRISIS,
        urgency=urgency,
        title_fr=f"{crisis_name} - {zone.name_fr}",
        summary_fr=_generate_crisis_summary(zone),
        zone_id=zone_id,
    )

    # Generer 2-3 suggestions
    dossier.suggestions = _generate_crisis_suggestions(zone_id, zone, state)

    return dossier


def _generate_crisis_summary(zone: Any) -> str:
    """Genere un resume narratif de la crise"""
    if zone.stability < 20:
        return f"La situation en {zone.name_fr} est critique. Sans intervention, l'effondrement est imminent."
    elif zone.has_crisis and zone.crisis_intensity > 60:
        return f"La crise en {zone.name_fr} s'intensifie. Les chancelleries s'affolent."
    elif zone.has_crisis:
        return f"Une crise couve en {zone.name_fr}. Le temps presse."
    else:
        return f"L'instabilite en {zone.name_fr} menace de degenerer."


def _generate_crisis_suggestions(zone_id: str, zone: Any, state: Any) -> List[SuggestedAction]:
    """Genere les suggestions pour une crise"""
    suggestions = []

    # Option 1: Intervention (agressive)
    suggestions.append(SuggestedAction(
        id=f"sug_{zone_id}_intervene",
        label="Intervenir",
        description_fr=f"Deployer des moyens en {zone.name_fr} pour stabiliser la situation",
        intention_type="MIL_REINFORCE",
        intention_id=f"reinforce_{zone_id}",
        target_zone=zone_id,
        political_cost=15,
        risk_level="medium",
        predicted_effects={
            "control_us": 10,
            "stability": 5,
            "world_tension": 10,
        },
    ))

    # Option 2: Diplomatie (moderee)
    suggestions.append(SuggestedAction(
        id=f"sug_{zone_id}_negotiate",
        label="Negocier",
        description_fr=f"Ouvrir des canaux diplomatiques pour desamorcer la crise",
        intention_type="DIPLO_NEGOTIATE",
        intention_id=f"negotiate_{zone_id}",
        target_zone=zone_id,
        political_cost=10,
        risk_level="low",
        predicted_effects={
            "stability": 10,
            "world_tension": -5,
        },
    ))

    # Option 3: Observer (passive mais info)
    if zone.stability > 15:  # Pas si critique
        suggestions.append(SuggestedAction(
            id=f"sug_{zone_id}_observe",
            label="Observer",
            description_fr=f"Renforcer le renseignement en {zone.name_fr} avant d'agir",
            intention_type="COV_INTEL",
            intention_id=f"intel_{zone_id}",
            target_zone=zone_id,
            political_cost=5,
            risk_level="low",
            predicted_effects={
                "intel": 15,
            },
        ))

    return suggestions


def _is_opportunity(zone: Any) -> bool:
    """Determine si une zone represente une opportunite"""
    # Zone contestee (proche de 50/50) avec stabilite correcte
    influence_diff = abs(zone.influence_us - zone.influence_ussr)
    return influence_diff < 20 and zone.stability > 40 and not zone.has_crisis


def _create_opportunity_dossier(zone_id: str, zone: Any, state: Any) -> Optional[UrgentDossier]:
    """Cree un dossier pour une opportunite"""

    # Determiner qui est en avance
    if zone.influence_us > zone.influence_ussr:
        lead = "americaine"
        urgency = DossierUrgency.MODERATE
    elif zone.influence_ussr > zone.influence_us:
        lead = "sovietique"
        urgency = DossierUrgency.HIGH  # Plus urgent si on est en retard
    else:
        lead = "nulle"
        urgency = DossierUrgency.MODERATE

    dossier = UrgentDossier(
        id=f"opportunity_{zone_id}",
        type=DossierType.OPPORTUNITY,
        urgency=urgency,
        title_fr=f"Opportunite - {zone.name_fr}",
        summary_fr=f"L'influence {lead} en {zone.name_fr} pourrait basculer. Le moment est propice.",
        zone_id=zone_id,
    )

    # Suggestions pour opportunite
    suggestions = []

    # Propaganda (soft power)
    suggestions.append(SuggestedAction(
        id=f"sug_{zone_id}_propaganda",
        label="Influence",
        description_fr=f"Renforcer notre presence culturelle et mediatique",
        intention_type="COV_PROPAGANDA",
        intention_id=f"propaganda_{zone_id}",
        target_zone=zone_id,
        political_cost=8,
        risk_level="low",
        predicted_effects={
            "influence_us": 10,
            "influence_ussr": -5,
        },
    ))

    # Economic aid
    suggestions.append(SuggestedAction(
        id=f"sug_{zone_id}_aid",
        label="Aide economique",
        description_fr=f"Proposer un programme d'aide au developpement",
        intention_type="ECON_AID",
        intention_id=f"aid_{zone_id}",
        target_zone=zone_id,
        political_cost=12,
        risk_level="low",
        predicted_effects={
            "influence_us": 15,
            "stability": 5,
        },
    ))

    dossier.suggestions = suggestions
    return dossier


def _create_internal_pressure_dossier(state: Any) -> Optional[UrgentDossier]:
    """Cree un dossier pour les pressions internes"""

    issues = []
    if state.player.domestic_stability < 40:
        issues.append("Opinion publique en berne")
    if state.player.political_capital < 30:
        issues.append("Capital politique epuise")
    if state.player.international_reputation < 40:
        issues.append("Reputation internationale degradee")

    if not issues:
        return None

    urgency = DossierUrgency.HIGH if state.player.domestic_stability < 30 else DossierUrgency.MODERATE

    dossier = UrgentDossier(
        id="internal_pressure",
        type=DossierType.PRESSURE,
        urgency=urgency,
        title_fr="Pressions internes",
        summary_fr=f"Le front interieur vacille: {', '.join(issues).lower()}.",
    )

    # Suggestions pour pressions internes
    suggestions = []

    if state.player.domestic_stability < 50:
        suggestions.append(SuggestedAction(
            id="sug_internal_speech",
            label="Discours",
            description_fr="Adresser la nation pour rassurer l'opinion",
            intention_type="DOMESTIC_SPEECH",
            intention_id="speech_nation",
            political_cost=5,
            risk_level="low",
            predicted_effects={
                "domestic_stability": 10,
            },
        ))

    if state.player.political_capital < 40:
        suggestions.append(SuggestedAction(
            id="sug_internal_consolidate",
            label="Consolider",
            description_fr="Recentrer les efforts sur le front interieur",
            intention_type="DOMESTIC_CONSOLIDATE",
            intention_id="consolidate",
            political_cost=0,  # Recuperation
            risk_level="low",
            predicted_effects={
                "political_capital": 15,
                "world_tension": -5,
            },
        ))

    dossier.suggestions = suggestions
    return dossier


def _can_negotiate(state: Any) -> bool:
    """Determine si une negociation est possible"""
    # Verifier la diplomatie avec l'URSS
    diplo = state.player.diplomacy.get("USSR")
    if not diplo:
        return False

    # Possible si trust > 20 et pas de tension extreme
    return diplo.trust > 20 and state.world_tension < 85


def _create_summit_dossier(state: Any) -> Optional[UrgentDossier]:
    """Cree un dossier pour une opportunite diplomatique"""

    diplo = state.player.diplomacy.get("USSR")
    if not diplo:
        return None

    urgency = DossierUrgency.LOW
    if state.world_tension > 60:
        urgency = DossierUrgency.MODERATE

    dossier = UrgentDossier(
        id="summit_opportunity",
        type=DossierType.SUMMIT,
        urgency=urgency,
        title_fr="Canal diplomatique",
        summary_fr="Moscou semble receptif. Une ouverture pourrait reduire les tensions.",
        actor_id="USSR",
    )

    suggestions = []

    # Proposition de sommet
    suggestions.append(SuggestedAction(
        id="sug_summit_propose",
        label="Proposer un sommet",
        description_fr="Inviter Khrouchtchev a des discussions directes",
        intention_type="DIPLO_SUMMIT",
        intention_id="summit_ussr",
        target_actor="USSR",
        political_cost=10,
        risk_level="low",
        predicted_effects={
            "trust": 10,
            "world_tension": -15,
        },
    ))

    # Message prive
    suggestions.append(SuggestedAction(
        id="sug_summit_backchannel",
        label="Message prive",
        description_fr="Utiliser les canaux secrets pour sonder les intentions",
        intention_type="DIPLO_BACKCHANNEL",
        intention_id="backchannel_ussr",
        target_actor="USSR",
        political_cost=5,
        risk_level="low",
        predicted_effects={
            "intel": 10,
            "trust": 5,
        },
    ))

    dossier.suggestions = suggestions
    return dossier


def _create_threat_dossier(state: Any) -> Optional[UrgentDossier]:
    """Cree un dossier pour une menace imminente"""

    if state.defcon <= 2:
        urgency = DossierUrgency.CRITICAL
        title = "Alerte nucleaire"
        summary = f"DEFCON {state.defcon}. Le monde est au bord du gouffre."
    else:
        urgency = DossierUrgency.HIGH
        title = "Escalade dangereuse"
        summary = f"Tension mondiale a {state.world_tension}%. L'escalade s'accelere."

    dossier = UrgentDossier(
        id="imminent_threat",
        type=DossierType.THREAT,
        urgency=urgency,
        title_fr=title,
        summary_fr=summary,
    )

    suggestions = []

    # De-escalade
    suggestions.append(SuggestedAction(
        id="sug_threat_deescalate",
        label="Desamorcer",
        description_fr="Gestes unilateraux pour reduire la tension",
        intention_type="DIPLO_DEESCALATE",
        intention_id="deescalate",
        political_cost=15,
        risk_level="low",
        predicted_effects={
            "world_tension": -20,
            "fear": -10,
        },
    ))

    # Posture defensive
    suggestions.append(SuggestedAction(
        id="sug_threat_defense",
        label="Posture defensive",
        description_fr="Renforcer les defenses sans provoquer",
        intention_type="MIL_DEFENSE",
        intention_id="defense_posture",
        political_cost=10,
        risk_level="medium",
        predicted_effects={
            "control_us": 5,
            "fear": 10,
        },
    ))

    # Telephone rouge
    if state.defcon <= 2:
        suggestions.append(SuggestedAction(
            id="sug_threat_hotline",
            label="Telephone rouge",
            description_fr="Contact direct avec le Kremlin - dernier recours",
            intention_type="DIPLO_HOTLINE",
            intention_id="hotline",
            target_actor="USSR",
            political_cost=5,
            risk_level="low",
            predicted_effects={
                "world_tension": -10,
                "defcon": 1,  # Peut ameliorer DEFCON
            },
        ))

    dossier.suggestions = suggestions
    return dossier
