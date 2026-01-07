"""Action Queue System for Historia Narrative (PaxHistoria Style)

Players accumulate actions in a queue before triggering a "Jump Forward"
that resolves all actions at once.

Key concepts:
- Actions are queued, not immediately executed
- Political capital is "reserved" when queueing
- Preview state shows what-if scenarios
- Adversary queue is hidden until jump
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueuedAction(BaseModel):
    """Action waiting in the queue"""
    id: str = Field(default_factory=lambda: str(uuid4())[:8])

    # Source
    intention_type: str
    intention_id: str
    source_text: str = ""

    # Target
    target_zone: Optional[str] = None
    target_actor: Optional[str] = None

    # Display
    description_fr: str
    description_en: str = ""

    # Preview hint (pressentiment narratif affiche avant Jump)
    # Ex: "La mer va devenir une frontiere." pour un blocus
    preview_hint_fr: Optional[str] = None

    # Cost (reserved when queued)
    political_cost: int = 0
    risk_level: str = "low"  # low, medium, high, extreme

    # Predicted effects (shown to player)
    predicted_effects: Dict[str, Any] = Field(default_factory=dict)

    # Timing
    queued_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 0  # Higher = processed first

    # State
    cancelled: bool = False


class ActionQueue(BaseModel):
    """Queue of player actions waiting for Jump Forward"""

    actions: List[QueuedAction] = Field(default_factory=list)

    # Capital tracking
    total_reserved_capital: int = 0
    available_capital: int = 100  # Will be set from player state

    def add(self, action: QueuedAction) -> tuple[bool, str]:
        """Add action to queue

        Returns (success, message)
        """
        # Check if we have enough capital
        if self.total_reserved_capital + action.political_cost > self.available_capital:
            deficit = (self.total_reserved_capital + action.political_cost) - self.available_capital
            return False, f"Capital insuffisant: {deficit} points manquants"

        # Check for duplicate targets (same zone, similar action)
        for existing in self.actions:
            if (existing.target_zone == action.target_zone and
                existing.intention_type == action.intention_type and
                not existing.cancelled):
                return False, f"Action similaire deja en queue pour {action.target_zone}"

        # Add to queue
        self.actions.append(action)
        self.total_reserved_capital += action.political_cost

        logger.info(f"Action queued: {action.intention_type} -> {action.target_zone or action.target_actor}")
        return True, "Action ajoutee a la queue"

    def remove(self, action_id: str) -> tuple[bool, str]:
        """Remove action from queue by ID

        Returns (success, message)
        """
        for i, action in enumerate(self.actions):
            if action.id == action_id:
                removed = self.actions.pop(i)
                self.total_reserved_capital -= removed.political_cost
                logger.info(f"Action removed: {removed.intention_type}")
                return True, "Action retiree"

        return False, "Action non trouvee"

    def clear(self):
        """Clear all actions from queue"""
        self.actions = []
        self.total_reserved_capital = 0
        logger.info("Action queue cleared")

    def get_active_actions(self) -> List[QueuedAction]:
        """Get all non-cancelled actions"""
        return [a for a in self.actions if not a.cancelled]

    def get_by_id(self, action_id: str) -> Optional[QueuedAction]:
        """Get action by ID"""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None

    def get_actions_for_zone(self, zone_id: str) -> List[QueuedAction]:
        """Get all actions targeting a specific zone"""
        return [a for a in self.get_active_actions() if a.target_zone == zone_id]

    def get_actions_by_type(self, action_type: str) -> List[QueuedAction]:
        """Get all actions of a specific type"""
        return [a for a in self.get_active_actions() if a.intention_type == action_type]

    def calculate_preview_effects(self) -> Dict[str, Any]:
        """Calculate cumulative effects if all actions were executed

        This is what-if preview shown to player before jump
        """
        effects = {
            "zones": {},
            "global": {
                "political_capital": -self.total_reserved_capital,
                "world_tension": 0,
                "defcon": 0,
            },
            "diplomacy": {},
            "risks": [],
        }

        for action in self.get_active_actions():
            # Zone effects
            if action.target_zone:
                if action.target_zone not in effects["zones"]:
                    effects["zones"][action.target_zone] = {
                        "influence_us": 0,
                        "control_us": 0,
                        "stability": 0,
                    }

                zone_fx = effects["zones"][action.target_zone]

                # Apply predicted effects
                for key, value in action.predicted_effects.items():
                    if key in zone_fx:
                        zone_fx[key] += value
                    elif key == "world_tension":
                        effects["global"]["world_tension"] += value
                    elif key == "defcon":
                        effects["global"]["defcon"] += value

            # Track high-risk actions
            if action.risk_level in ["high", "extreme"]:
                effects["risks"].append({
                    "action_id": action.id,
                    "description": action.description_fr,
                    "risk_level": action.risk_level,
                })

        return effects

    def get_queue_summary(self) -> Dict[str, Any]:
        """Get summary of current queue state"""
        active = self.get_active_actions()

        by_type = {}
        for action in active:
            cat = action.intention_type.split("_")[0]  # DIPLO, MIL, COV, etc.
            by_type[cat] = by_type.get(cat, 0) + 1

        by_zone = {}
        for action in active:
            if action.target_zone:
                by_zone[action.target_zone] = by_zone.get(action.target_zone, 0) + 1

        risk_counts = {"low": 0, "medium": 0, "high": 0, "extreme": 0}
        for action in active:
            risk_counts[action.risk_level] = risk_counts.get(action.risk_level, 0) + 1

        return {
            "count": len(active),
            "total_cost": self.total_reserved_capital,
            "remaining_capital": self.available_capital - self.total_reserved_capital,
            "by_type": by_type,
            "by_zone": by_zone,
            "risk_breakdown": risk_counts,
            "has_high_risk": risk_counts["high"] > 0 or risk_counts["extreme"] > 0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize queue to dict"""
        return {
            "actions": [a.model_dump() for a in self.actions],
            "total_reserved_capital": self.total_reserved_capital,
            "available_capital": self.available_capital,
            "summary": self.get_queue_summary(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionQueue":
        """Deserialize queue from dict"""
        queue = cls()
        queue.available_capital = data.get("available_capital", 100)
        queue.total_reserved_capital = data.get("total_reserved_capital", 0)
        queue.actions = [QueuedAction(**a) for a in data.get("actions", [])]
        return queue


# =============================================================================
# PREVIEW HINTS - Pressentiments narratifs (pas de chiffres!)
# =============================================================================
# Affiches AVANT le Jump pour que le joueur sente l'impact sans what-if numerique

PREVIEW_HINTS = {
    # Military actions
    "MIL_BLOCKADE": [
        "La mer va devenir une frontiere.",
        "Les navires attendent votre ordre.",
        "Le blocus est une declaration sans mots.",
    ],
    "MIL_REINFORCE": [
        "Les troupes se deploient en silence.",
        "Chaque soldat envoye est un message.",
        "La presence militaire dit ce que la diplomatie ne peut pas.",
    ],
    "MIL_DEMO": [
        "Le tonnerre des armes parlera pour vous.",
        "Une demonstration de force. Rien de plus... pour l'instant.",
        "Ils verront votre puissance. Ils comprendront.",
    ],
    "MIL_THREAT": [
        "Les mots peuvent tuer, parfois.",
        "Une menace n'est efficace que si l'on croit qu'elle sera executee.",
        "Le doute que vous semez vaut mille soldats.",
    ],

    # Diplomatic actions
    "DIPLO_BACKCHANNEL": [
        "Une porte reste entrouverte.",
        "Dans l'ombre, quelqu'un ecoute encore.",
        "Les vrais messages passent loin des cameras.",
    ],
    "DIPLO_SUMMIT": [
        "Face a face. Les yeux ne mentent pas.",
        "Un sommet peut tout changer. Ou rien.",
        "Quand les dirigeants se regardent, le monde retient son souffle.",
    ],
    "DIPLO_CONCESSION": [
        "Ceder pour mieux tenir.",
        "Un compromis n'est pas une defaite.",
        "Parfois, plier evite de rompre.",
    ],
    "DIPLO_ULTIMATUM": [
        "Les mots ultimes. Apres, il n'y a que l'acte.",
        "Un ultimatum ne se retire pas.",
        "La ligne rouge est tracee. Elle ne bougera plus.",
    ],

    # Covert actions
    "COV_INTEL": [
        "Savoir, c'est pouvoir. Mais pas encore agir.",
        "Les ombres collectent ce que la lumiere ignore.",
        "Plus vous savez, plus vos choix seront clairs.",
    ],
    "COV_DESTAB": [
        "Les graines du chaos sont semees.",
        "Ce qui semble stable peut s'effondrer vite.",
        "Dans le noir, des mains travaillent.",
    ],
    "COV_PROPAGANDA": [
        "Les mots sont des armes silencieuses.",
        "Changer les esprits prend du temps. Mais ca dure.",
        "La verite a plusieurs visages. Choisissez lequel montrer.",
    ],

    # Economic actions
    "ECO_AID": [
        "L'argent achete l'amitie. Parfois.",
        "Un investissement dans le futur... politique.",
        "Chaque dollar envoye est un fil invisible.",
    ],
    "ECO_SANCTION": [
        "L'economie peut etrangler sans bruit.",
        "Les sanctions sont une guerre lente.",
        "Priver, c'est affaiblir. Mais la haine grandit aussi.",
    ],

    # Crisis management
    "CRISIS_DEESCALATE": [
        "Reculer n'est pas toujours perdre.",
        "Parfois, le plus brave est celui qui s'arrete.",
        "La desescalade demande plus de courage que l'attaque.",
    ],
    "CRISIS_ESCALATE": [
        "Monter les encheres. Mais qui suivra?",
        "L'escalade est un jeu sans gagnant assure.",
        "Plus haut. Plus fort. Plus dangereux.",
    ],
}


def get_preview_hint(intention_type: str) -> Optional[str]:
    """
    Retourne un pressentiment narratif pour une action.

    Le joueur voit ce hint AVANT le Jump pour comprendre
    qualitativement l'impact de son action.

    Args:
        intention_type: Type d'intention (MIL_BLOCKADE, DIPLO_SUMMIT, etc.)

    Returns:
        String du hint ou None si pas de hint disponible
    """
    import random

    hints = PREVIEW_HINTS.get(intention_type, [])
    if not hints:
        # Fallback par categorie
        category = intention_type.split("_")[0] if "_" in intention_type else intention_type
        category_fallbacks = {
            "MIL": ["Force projetee. Message envoye."],
            "DIPLO": ["Les mots sont en mouvement."],
            "COV": ["Dans l'ombre, les rouages tournent."],
            "ECO": ["L'argent parle sa propre langue."],
            "CRISIS": ["Le monde attend votre choix."],
        }
        hints = category_fallbacks.get(category, [])

    return random.choice(hints) if hints else None


def create_queued_action(
    intention_type: str,
    intention_id: str,
    description_fr: str,
    political_cost: int,
    risk_level: str = "low",
    target_zone: Optional[str] = None,
    target_actor: Optional[str] = None,
    predicted_effects: Optional[Dict[str, Any]] = None,
    source_text: str = "",
) -> QueuedAction:
    """Factory function to create a QueuedAction with auto-generated preview hint"""
    return QueuedAction(
        intention_type=intention_type,
        intention_id=intention_id,
        description_fr=description_fr,
        political_cost=political_cost,
        risk_level=risk_level,
        target_zone=target_zone,
        target_actor=target_actor,
        predicted_effects=predicted_effects or {},
        source_text=source_text,
        preview_hint_fr=get_preview_hint(intention_type),
    )
