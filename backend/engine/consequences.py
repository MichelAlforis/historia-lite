"""Consequence prediction system for Historia Lite"""
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConsequencePrediction(BaseModel):
    """Predicted consequences of an action"""
    action: str
    target_id: Optional[str] = None

    # Predicted changes
    relation_changes: Dict[str, int] = Field(default_factory=dict)
    stat_changes: Dict[str, int] = Field(default_factory=dict)
    global_tension_change: int = 0

    # Risk assessment
    war_risk: int = 0  # 0-100
    sanctions_risk: int = 0
    stability_risk: int = 0

    # Summary
    severity: str = "low"  # low, medium, high, critical
    description: str = ""
    description_fr: str = ""


class ConsequenceCalculator:
    """Calculates predicted consequences of actions"""

    def predict_action(
        self,
        actor_id: str,
        action: str,
        target_id: Optional[str],
        world
    ) -> ConsequencePrediction:
        """Predict consequences of an action"""

        actor = world.get_country(actor_id)
        target = world.get_country(target_id) if target_id else None

        if not actor:
            return ConsequencePrediction(action=action)

        if action == "declare_war":
            return self._predict_war(actor, target, world)
        elif action == "impose_sanctions":
            return self._predict_sanctions(actor, target, world)
        elif action == "form_alliance":
            return self._predict_alliance(actor, target, world)
        elif action == "nuclear_test":
            return self._predict_nuclear_test(actor, world)
        else:
            return ConsequencePrediction(
                action=action,
                target_id=target_id,
                description=f"Unknown action: {action}",
                description_fr=f"Action inconnue: {action}"
            )

    def _predict_war(self, actor, target, world) -> ConsequencePrediction:
        """Predict consequences of declaring war"""
        if not target:
            return ConsequencePrediction(action="declare_war")

        relation_changes = {target.id: -100}

        # Target's allies will turn hostile
        for ally_id in target.allies:
            relation_changes[ally_id] = -50

        # Global tension increase
        tension_change = 15
        if actor.tier == 1 or target.tier == 1:
            tension_change = 30

        return ConsequencePrediction(
            action="declare_war",
            target_id=target.id,
            relation_changes=relation_changes,
            stat_changes={"stability": -10, "economy": -5},
            global_tension_change=tension_change,
            war_risk=100,
            sanctions_risk=60,
            stability_risk=30,
            severity="critical",
            description=f"War with {target.name} will damage relations and economy",
            description_fr=f"La guerre avec {target.name_fr} nuira aux relations et a l'economie"
        )

    def _predict_sanctions(self, actor, target, world) -> ConsequencePrediction:
        """Predict consequences of imposing sanctions"""
        if not target:
            return ConsequencePrediction(action="impose_sanctions")

        return ConsequencePrediction(
            action="impose_sanctions",
            target_id=target.id,
            relation_changes={target.id: -30},
            global_tension_change=5,
            sanctions_risk=20,
            severity="medium",
            description=f"Sanctions on {target.name} will strain relations",
            description_fr=f"Les sanctions contre {target.name_fr} tendront les relations"
        )

    def _predict_alliance(self, actor, target, world) -> ConsequencePrediction:
        """Predict consequences of forming alliance"""
        if not target:
            return ConsequencePrediction(action="form_alliance")

        # Target's rivals will be unhappy
        relation_changes = {target.id: 30}
        for rival_id in target.rivals:
            relation_changes[rival_id] = -15

        return ConsequencePrediction(
            action="form_alliance",
            target_id=target.id,
            relation_changes=relation_changes,
            global_tension_change=-2,
            severity="low",
            description=f"Alliance with {target.name} will improve security",
            description_fr=f"L'alliance avec {target.name_fr} ameliorera la securite"
        )

    def _predict_nuclear_test(self, actor, world) -> ConsequencePrediction:
        """Predict consequences of nuclear test"""

        relation_changes = {}
        # Major powers will condemn
        for country in world.get_countries_list():
            if country.tier <= 2 and country.id != actor.id:
                relation_changes[country.id] = -20

        return ConsequencePrediction(
            action="nuclear_test",
            relation_changes=relation_changes,
            stat_changes={"nuclear": 5},
            global_tension_change=10,
            sanctions_risk=70,
            severity="high",
            description="Nuclear test will trigger international condemnation",
            description_fr="Le test nucleaire declenchera une condamnation internationale"
        )


# Global instance
consequence_calculator = ConsequenceCalculator()
