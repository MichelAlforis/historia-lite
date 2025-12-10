"""Dilemma detection and resolution system"""
import json
import logging
import random
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

from schemas.interaction import (
    ActiveDilemma,
    DilemmaChoice,
    DilemmaTemplate,
    DilemmaType,
    DilemmaResolveResponse,
)
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


class DilemmaManager:
    """Manages dilemma detection, creation, and resolution"""

    def __init__(self):
        self.templates: Dict[str, DilemmaTemplate] = {}
        self.pending_dilemmas: Dict[str, ActiveDilemma] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default dilemma templates"""
        self.templates = {
            # Economic dilemmas
            "economic_crisis": DilemmaTemplate(
                id="economic_crisis",
                type=DilemmaType.ECONOMIC_CRISIS,
                title="Economic Crisis",
                title_fr="Crise Economique",
                description="Your economy is collapsing. Drastic measures are needed.",
                description_fr="Votre economie s'effondre. Des mesures drastiques sont necessaires.",
                trigger_condition="economy < 20",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Austerity Measures",
                        label_fr="Mesures d'austerite",
                        description="Cut government spending drastically",
                        description_fr="Reduire drastiquement les depenses publiques",
                        effects={"economy": 10, "stability": -15},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="International Bailout",
                        label_fr="Plan de sauvetage international",
                        description="Accept foreign financial aid with conditions",
                        description_fr="Accepter une aide financiere etrangere avec conditions",
                        effects={"economy": 15, "soft_power": -10},
                        relation_effects={"USA": 10, "EU": 10}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Default on Debt",
                        label_fr="Defaut de paiement",
                        description="Refuse to pay debts, reset economy",
                        description_fr="Refuser de payer les dettes, reset economique",
                        effects={"economy": -5, "stability": -5},
                        relation_effects={"USA": -20, "EU": -20, "CHN": -15}
                    )
                ]
            ),
            "budget_shortage": DilemmaTemplate(
                id="budget_shortage",
                type=DilemmaType.BUDGET_SHORTAGE,
                title="Budget Shortage",
                title_fr="Penurie Budgetaire",
                description="Your major project needs more funding.",
                description_fr="Votre projet majeur necessite plus de financement.",
                trigger_condition="project_underfunded",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Raise Taxes",
                        label_fr="Augmenter les impots",
                        description="Increase taxes to fund the project",
                        description_fr="Augmenter les impots pour financer le projet",
                        effects={"economy": 5, "stability": -10},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Cut Other Programs",
                        label_fr="Couper d'autres programmes",
                        description="Redirect funds from education and health",
                        description_fr="Rediriger les fonds de l'education et de la sante",
                        effects={"technology": -5, "stability": -5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Delay Project",
                        label_fr="Retarder le projet",
                        description="Extend the project timeline by 2 years",
                        description_fr="Prolonger le projet de 2 ans",
                        effects={"soft_power": -5},
                        relation_effects={}
                    )
                ]
            ),
            # Military dilemmas
            "war_declaration": DilemmaTemplate(
                id="war_declaration",
                type=DilemmaType.WAR_DECLARATION,
                title="War Declaration",
                title_fr="Declaration de Guerre",
                description="An enemy has declared war on you!",
                description_fr="Un ennemi vous a declare la guerre!",
                trigger_condition="war_declared_against",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Full Mobilization",
                        label_fr="Mobilisation totale",
                        description="Mobilize all forces for war",
                        description_fr="Mobiliser toutes les forces pour la guerre",
                        effects={"military": 15, "economy": -15, "stability": -5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Defensive Stance",
                        label_fr="Position defensive",
                        description="Focus on defense while seeking allies",
                        description_fr="Se concentrer sur la defense tout en cherchant des allies",
                        effects={"military": 5, "economy": -5},
                        relation_effects={"USA": 5, "EU": 5}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Seek Peace",
                        label_fr="Chercher la paix",
                        description="Immediately offer peace negotiations",
                        description_fr="Proposer immediatement des negociations de paix",
                        effects={"stability": 5, "soft_power": -10},
                        relation_effects={},
                        ends_war=True
                    )
                ]
            ),
            "ally_attacked": DilemmaTemplate(
                id="ally_attacked",
                type=DilemmaType.ALLY_ATTACKED,
                title="Ally Under Attack",
                title_fr="Allie Attaque",
                description="Your ally has been attacked and requests military support.",
                description_fr="Votre allie a ete attaque et demande un soutien militaire.",
                trigger_condition="ally_at_war",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Full Military Support",
                        label_fr="Soutien militaire total",
                        description="Join the war on your ally's side",
                        description_fr="Rejoindre la guerre aux cotes de votre allie",
                        effects={"military": -15, "economy": -10},
                        relation_effects={},  # Dynamic based on ally
                        declares_war=None  # Dynamic
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Economic Support Only",
                        label_fr="Soutien economique uniquement",
                        description="Send financial and humanitarian aid",
                        description_fr="Envoyer une aide financiere et humanitaire",
                        effects={"economy": -5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Stay Neutral",
                        label_fr="Rester neutre",
                        description="Refuse to get involved",
                        description_fr="Refuser de s'impliquer",
                        effects={"stability": 5},
                        relation_effects={},
                        triggers_event="alliance_strain"
                    )
                ]
            ),
            "nuclear_threat": DilemmaTemplate(
                id="nuclear_threat",
                type=DilemmaType.NUCLEAR_THREAT,
                title="Nuclear Threat",
                title_fr="Menace Nucleaire",
                description="A nuclear power is threatening to use nuclear weapons.",
                description_fr="Une puissance nucleaire menace d'utiliser des armes nucleaires.",
                trigger_condition="nuclear_escalation",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Nuclear Alert",
                        label_fr="Alerte nucleaire",
                        description="Raise nuclear alert level, prepare retaliation",
                        description_fr="Elever le niveau d'alerte nucleaire, preparer la riposte",
                        effects={"military": 10, "stability": -20},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="International Pressure",
                        label_fr="Pression internationale",
                        description="Rally the international community",
                        description_fr="Rallier la communaute internationale",
                        effects={"soft_power": 10},
                        relation_effects={"USA": 10, "EU": 10, "CHN": 5}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Direct Negotiation",
                        label_fr="Negociation directe",
                        description="Open direct talks with the threat source",
                        description_fr="Ouvrir des pourparlers directs avec la source de la menace",
                        effects={"soft_power": -5, "stability": 5},
                        relation_effects={}
                    )
                ]
            ),
            # Stability dilemmas
            "revolution_risk": DilemmaTemplate(
                id="revolution_risk",
                type=DilemmaType.REVOLUTION_RISK,
                title="Revolution Risk",
                title_fr="Risque de Revolution",
                description="Civil unrest is reaching dangerous levels.",
                description_fr="L'agitation civile atteint des niveaux dangereux.",
                trigger_condition="stability < 25",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Martial Law",
                        label_fr="Loi martiale",
                        description="Deploy military to restore order",
                        description_fr="Deployer l'armee pour retablir l'ordre",
                        effects={"stability": 15, "soft_power": -15},
                        relation_effects={"USA": -10, "EU": -10}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Political Reforms",
                        label_fr="Reformes politiques",
                        description="Address grievances with reforms",
                        description_fr="Repondre aux griefs par des reformes",
                        effects={"stability": 10, "economy": -5},
                        relation_effects={"USA": 5, "EU": 5}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="National Address",
                        label_fr="Discours national",
                        description="Appeal directly to the people",
                        description_fr="Faire appel directement au peuple",
                        effects={"stability": 5, "soft_power": 5},
                        relation_effects={}
                    )
                ]
            ),
            "coup_attempt": DilemmaTemplate(
                id="coup_attempt",
                type=DilemmaType.COUP_ATTEMPT,
                title="Coup Attempt",
                title_fr="Tentative de Coup d'Etat",
                description="Military officers are plotting against the government.",
                description_fr="Des officiers militaires complotent contre le gouvernement.",
                trigger_condition="stability < 15 and military > 50",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Purge Military",
                        label_fr="Purger l'armee",
                        description="Arrest conspirators and loyalists",
                        description_fr="Arreter les conspirateurs et les loyalistes",
                        effects={"military": -20, "stability": 10},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Negotiate",
                        label_fr="Negocier",
                        description="Offer concessions to plotters",
                        description_fr="Offrir des concessions aux comploteurs",
                        effects={"stability": -5, "military": 5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Foreign Help",
                        label_fr="Aide etrangere",
                        description="Request foreign intervention",
                        description_fr="Demander une intervention etrangere",
                        effects={"stability": 5, "soft_power": -15},
                        relation_effects={"USA": 15}
                    )
                ]
            ),
            # Diplomatic dilemmas
            "ultimatum_received": DilemmaTemplate(
                id="ultimatum_received",
                type=DilemmaType.ULTIMATUM_RECEIVED,
                title="Ultimatum Received",
                title_fr="Ultimatum Recu",
                description="A foreign power demands you comply or face consequences.",
                description_fr="Une puissance etrangere exige que vous vous conformiez ou subissiez les consequences.",
                trigger_condition="ultimatum_sent",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Mobilize for War",
                        label_fr="Mobiliser pour la guerre",
                        description="Reject ultimatum and prepare for conflict",
                        description_fr="Rejeter l'ultimatum et se preparer au conflit",
                        effects={"military": 15, "economy": -10, "stability": -5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Seek Mediation",
                        label_fr="Chercher une mediation",
                        description="Request international mediation",
                        description_fr="Demander une mediation internationale",
                        effects={"soft_power": 5},
                        relation_effects={"USA": 10, "EU": 10}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Accept Terms",
                        label_fr="Accepter les termes",
                        description="Comply with the demands",
                        description_fr="Se conformer aux exigences",
                        effects={"stability": -15, "soft_power": -10},
                        relation_effects={}
                    )
                ]
            ),
            "alliance_request": DilemmaTemplate(
                id="alliance_request",
                type=DilemmaType.ALLIANCE_REQUEST,
                title="Alliance Request",
                title_fr="Demande d'Alliance",
                description="A nation wants to form an alliance with you.",
                description_fr="Une nation souhaite former une alliance avec vous.",
                trigger_condition="alliance_proposed",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Accept Alliance",
                        label_fr="Accepter l'alliance",
                        description="Form a full military alliance",
                        description_fr="Former une alliance militaire complete",
                        effects={"soft_power": 5},
                        relation_effects={}  # Dynamic based on proposer
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Limited Partnership",
                        label_fr="Partenariat limite",
                        description="Agree to economic cooperation only",
                        description_fr="Accepter uniquement une cooperation economique",
                        effects={"economy": 5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Decline",
                        label_fr="Decliner",
                        description="Politely refuse the offer",
                        description_fr="Refuser poliment l'offre",
                        effects={},
                        relation_effects={}
                    )
                ]
            ),
            "sanctions_imposed": DilemmaTemplate(
                id="sanctions_imposed",
                type=DilemmaType.SANCTIONS_IMPOSED,
                title="Sanctions Imposed",
                title_fr="Sanctions Imposees",
                description="Major powers have imposed economic sanctions on you.",
                description_fr="Les grandes puissances ont impose des sanctions economiques.",
                trigger_condition="sanctions_received",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Defy Sanctions",
                        label_fr="Defier les sanctions",
                        description="Continue current policies despite sanctions",
                        description_fr="Poursuivre les politiques actuelles malgre les sanctions",
                        effects={"economy": -10, "stability": 5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Seek Alternatives",
                        label_fr="Chercher des alternatives",
                        description="Turn to other trading partners",
                        description_fr="Se tourner vers d'autres partenaires commerciaux",
                        effects={"economy": -5},
                        relation_effects={"CHN": 10, "RUS": 10}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Negotiate Removal",
                        label_fr="Negocier le retrait",
                        description="Make concessions to lift sanctions",
                        description_fr="Faire des concessions pour lever les sanctions",
                        effects={"soft_power": -10},
                        relation_effects={"USA": 15, "EU": 15}
                    )
                ]
            ),
            # Project dilemmas
            "project_milestone": DilemmaTemplate(
                id="project_milestone",
                type=DilemmaType.PROJECT_MILESTONE,
                title="Project Milestone",
                title_fr="Jalon du Projet",
                description="Your major project has reached a critical milestone.",
                description_fr="Votre projet majeur a atteint un jalon critique.",
                trigger_condition="milestone_reached",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Accelerate",
                        label_fr="Accelerer",
                        description="Invest more to speed up completion",
                        description_fr="Investir plus pour accelerer l'achevement",
                        effects={"economy": -10},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Maintain Pace",
                        label_fr="Maintenir le rythme",
                        description="Continue at current pace",
                        description_fr="Continuer au rythme actuel",
                        effects={},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Publicize Success",
                        label_fr="Publiciser le succes",
                        description="Make a big announcement for prestige",
                        description_fr="Faire une grande annonce pour le prestige",
                        effects={"soft_power": 10, "stability": 5},
                        relation_effects={}
                    )
                ]
            ),
            "project_sabotage": DilemmaTemplate(
                id="project_sabotage",
                type=DilemmaType.PROJECT_SABOTAGE,
                title="Project Sabotaged",
                title_fr="Projet Sabote",
                description="Your project has been sabotaged by foreign agents.",
                description_fr="Votre projet a ete sabote par des agents etrangers.",
                trigger_condition="project_sabotaged",
                choices=[
                    DilemmaChoice(
                        id=1,
                        label="Retaliate",
                        label_fr="Riposter",
                        description="Launch counter-intelligence operation",
                        description_fr="Lancer une operation de contre-espionnage",
                        effects={"technology": 5, "economy": -5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=2,
                        label="Rebuild Quietly",
                        label_fr="Reconstruire discretement",
                        description="Repair damage without escalation",
                        description_fr="Reparer les degats sans escalade",
                        effects={"economy": -5},
                        relation_effects={}
                    ),
                    DilemmaChoice(
                        id=3,
                        label="Public Accusation",
                        label_fr="Accusation publique",
                        description="Publicly accuse the responsible nation",
                        description_fr="Accuser publiquement la nation responsable",
                        effects={"soft_power": 5},
                        relation_effects={}
                    )
                ]
            ),
        }

    def load_templates_from_file(self, file_path: Path) -> None:
        """Load dilemma templates from JSON file"""
        if not file_path.exists():
            logger.warning(f"Dilemmas file not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for dilemma_data in data.get("dilemmas", []):
            choices = [DilemmaChoice(**c) for c in dilemma_data.pop("choices", [])]
            template = DilemmaTemplate(**dilemma_data, choices=choices)
            self.templates[template.id] = template

        logger.info(f"Loaded {len(self.templates)} dilemma templates")

    def detect_dilemmas(
        self,
        country: "Country",
        world: "World",
        active_projects: List = None
    ) -> List[ActiveDilemma]:
        """Detect if any dilemma conditions are met for a country"""
        detected = []

        # Economic crisis
        if country.economy < 20:
            if not self._has_pending_dilemma(country.id, DilemmaType.ECONOMIC_CRISIS):
                dilemma = self._create_dilemma(
                    "economic_crisis", country, world,
                    trigger_data={"economy_level": country.economy}
                )
                if dilemma:
                    detected.append(dilemma)

        # Revolution risk
        if country.stability < 25:
            if not self._has_pending_dilemma(country.id, DilemmaType.REVOLUTION_RISK):
                dilemma = self._create_dilemma(
                    "revolution_risk", country, world,
                    trigger_data={"stability_level": country.stability}
                )
                if dilemma:
                    detected.append(dilemma)

        # Coup attempt (low stability + high military)
        if country.stability < 15 and country.military > 50:
            if not self._has_pending_dilemma(country.id, DilemmaType.COUP_ATTEMPT):
                dilemma = self._create_dilemma(
                    "coup_attempt", country, world,
                    trigger_data={
                        "stability_level": country.stability,
                        "military_level": country.military
                    }
                )
                if dilemma:
                    detected.append(dilemma)

        # Ally attacked
        for ally_id in country.allies:
            ally = world.countries.get(ally_id)
            if ally and ally.at_war:
                for attacker_id in ally.at_war:
                    if attacker_id not in country.at_war:
                        if not self._has_pending_dilemma(
                            country.id, DilemmaType.ALLY_ATTACKED
                        ):
                            dilemma = self._create_dilemma(
                                "ally_attacked", country, world,
                                trigger_data={
                                    "ally_id": ally_id,
                                    "attacker_id": attacker_id
                                },
                                related_country_id=ally_id
                            )
                            if dilemma:
                                detected.append(dilemma)

        # War declared on this country
        if country.at_war:
            for enemy_id in country.at_war:
                if not self._has_pending_dilemma(
                    country.id, DilemmaType.WAR_DECLARATION
                ):
                    dilemma = self._create_dilemma(
                        "war_declaration", country, world,
                        trigger_data={"enemy_id": enemy_id},
                        related_country_id=enemy_id
                    )
                    if dilemma:
                        detected.append(dilemma)
                    break

        # Sanctions imposed
        sanctioned_by = []
        for other_id, other in world.countries.items():
            if country.id in other.sanctions_on:
                sanctioned_by.append(other_id)

        if sanctioned_by and not self._has_pending_dilemma(
            country.id, DilemmaType.SANCTIONS_IMPOSED
        ):
            dilemma = self._create_dilemma(
                "sanctions_imposed", country, world,
                trigger_data={"sanctioned_by": sanctioned_by}
            )
            if dilemma:
                detected.append(dilemma)

        return detected

    def _has_pending_dilemma(self, country_id: str, dilemma_type: DilemmaType) -> bool:
        """Check if country already has a pending dilemma of this type"""
        for dilemma in self.pending_dilemmas.values():
            if dilemma.country_id == country_id and dilemma.type == dilemma_type:
                if dilemma.status == "pending":
                    return True
        return False

    def _create_dilemma(
        self,
        template_id: str,
        country: "Country",
        world: "World",
        trigger_data: Dict = None,
        related_country_id: str = None,
        related_project_id: str = None
    ) -> Optional[ActiveDilemma]:
        """Create an active dilemma from template"""
        template = self.templates.get(template_id)
        if not template:
            return None

        dilemma_id = f"dilemma_{template_id}_{country.id}_{uuid.uuid4().hex[:8]}"

        # Customize description with context
        description = template.description
        description_fr = template.description_fr

        if trigger_data:
            if "ally_id" in trigger_data:
                ally = world.countries.get(trigger_data["ally_id"])
                if ally:
                    description = f"{ally.name} has been attacked and requests your help!"
                    description_fr = f"{ally.name_fr} a ete attaque et demande votre aide!"

            if "enemy_id" in trigger_data:
                enemy = world.countries.get(trigger_data["enemy_id"])
                if enemy:
                    description = f"{enemy.name} has declared war on you!"
                    description_fr = f"{enemy.name_fr} vous a declare la guerre!"

            if "sanctioned_by" in trigger_data:
                sanctioners = trigger_data["sanctioned_by"]
                if len(sanctioners) > 2:
                    description = f"Multiple nations have imposed sanctions on you."
                    description_fr = f"Plusieurs nations ont impose des sanctions."
                else:
                    names = [world.countries.get(s, {}).name for s in sanctioners if world.countries.get(s)]
                    description = f"{', '.join(names)} imposed sanctions on you."
                    description_fr = f"{', '.join(names)} ont impose des sanctions."

        # Copy choices and customize if needed
        choices = []
        for choice in template.choices:
            new_choice = DilemmaChoice(
                id=choice.id,
                label=choice.label,
                label_fr=choice.label_fr,
                description=choice.description,
                description_fr=choice.description_fr,
                effects=dict(choice.effects),
                relation_effects=dict(choice.relation_effects),
                triggers_event=choice.triggers_event,
                starts_project=choice.starts_project,
                ends_war=choice.ends_war,
                declares_war=choice.declares_war
            )

            # Dynamic relation effects for ally_attacked
            if template_id == "ally_attacked" and trigger_data:
                ally_id = trigger_data.get("ally_id")
                attacker_id = trigger_data.get("attacker_id")
                if ally_id and attacker_id:
                    if choice.id == 1:  # Full support
                        new_choice.relation_effects[ally_id] = 40
                        new_choice.relation_effects[attacker_id] = -50
                        new_choice.declares_war = attacker_id
                    elif choice.id == 2:  # Economic support
                        new_choice.relation_effects[ally_id] = 15
                        new_choice.relation_effects[attacker_id] = -20
                    elif choice.id == 3:  # Stay neutral
                        new_choice.relation_effects[ally_id] = -30
                        new_choice.relation_effects[attacker_id] = 10

            choices.append(new_choice)

        dilemma = ActiveDilemma(
            id=dilemma_id,
            template_id=template_id,
            type=template.type,
            title=template.title,
            title_fr=template.title_fr,
            description=description,
            description_fr=description_fr,
            country_id=country.id,
            year_triggered=world.year,
            trigger_data=trigger_data or {},
            related_country_id=related_country_id,
            related_project_id=related_project_id,
            choices=choices,
            expires_at_year=world.year + (template.expires_after_years or 2),
            auto_choice=template.auto_choice,
            status="pending"
        )

        self.pending_dilemmas[dilemma_id] = dilemma
        logger.info(f"Created dilemma {dilemma_id} for {country.id}: {template.title}")
        return dilemma

    def resolve_dilemma(
        self,
        dilemma_id: str,
        choice_id: int,
        country: "Country",
        world: "World"
    ) -> Optional[DilemmaResolveResponse]:
        """Resolve a dilemma with the player's choice"""
        dilemma = self.pending_dilemmas.get(dilemma_id)
        if not dilemma:
            logger.warning(f"Dilemma not found: {dilemma_id}")
            return None

        if dilemma.status != "pending":
            logger.warning(f"Dilemma already resolved: {dilemma_id}")
            return None

        if dilemma.country_id != country.id:
            logger.warning(f"Dilemma {dilemma_id} does not belong to {country.id}")
            return None

        # Find the chosen option
        chosen = None
        for choice in dilemma.choices:
            if choice.id == choice_id:
                chosen = choice
                break

        if not chosen:
            logger.warning(f"Invalid choice {choice_id} for dilemma {dilemma_id}")
            return None

        # Apply effects
        effects_applied = {}
        for stat, value in chosen.effects.items():
            current = getattr(country, stat, None)
            if current is not None:
                new_value = max(0, min(100, current + value))
                setattr(country, stat, new_value)
                effects_applied[stat] = value

        # Apply relation effects
        relation_changes = {}
        for target_id, change in chosen.relation_effects.items():
            if target_id in country.relations:
                old_rel = country.relations[target_id]
                new_rel = max(-100, min(100, old_rel + change))
                country.relations[target_id] = new_rel
                relation_changes[target_id] = change

        # Handle special consequences
        events_triggered = []

        if chosen.declares_war:
            if chosen.declares_war not in country.at_war:
                country.at_war.append(chosen.declares_war)
                target = world.countries.get(chosen.declares_war)
                if target and country.id not in target.at_war:
                    target.at_war.append(country.id)
                events_triggered.append({
                    "type": "war_declaration",
                    "attacker": country.id,
                    "defender": chosen.declares_war
                })

        if chosen.ends_war:
            # End war with related country
            if dilemma.related_country_id:
                if dilemma.related_country_id in country.at_war:
                    country.at_war.remove(dilemma.related_country_id)
                    target = world.countries.get(dilemma.related_country_id)
                    if target and country.id in target.at_war:
                        target.at_war.remove(country.id)
                    events_triggered.append({
                        "type": "peace",
                        "parties": [country.id, dilemma.related_country_id]
                    })

        if chosen.triggers_event:
            events_triggered.append({
                "type": chosen.triggers_event,
                "country": country.id
            })

        # Mark dilemma as resolved
        dilemma.status = "resolved"
        dilemma.chosen_option = choice_id

        # Generate response message
        message = f"You chose: {chosen.label}"
        message_fr = f"Vous avez choisi: {chosen.label_fr}"

        if effects_applied:
            effects_str = ", ".join([f"{k}: {'+' if v > 0 else ''}{v}" for k, v in effects_applied.items()])
            message += f". Effects: {effects_str}"
            message_fr += f". Effets: {effects_str}"

        logger.info(f"Resolved dilemma {dilemma_id}: choice {choice_id}")

        return DilemmaResolveResponse(
            dilemma_id=dilemma_id,
            choice_made=chosen,
            effects_applied=effects_applied,
            relation_changes=relation_changes,
            events_triggered=events_triggered,
            message=message,
            message_fr=message_fr
        )

    def get_pending_dilemmas(self, country_id: str) -> List[ActiveDilemma]:
        """Get all pending dilemmas for a country"""
        return [
            d for d in self.pending_dilemmas.values()
            if d.country_id == country_id and d.status == "pending"
        ]

    def get_dilemma_history(self, country_id: str) -> List[ActiveDilemma]:
        """Get resolved dilemmas for a country"""
        return [
            d for d in self.pending_dilemmas.values()
            if d.country_id == country_id and d.status == "resolved"
        ]

    def process_expirations(self, world: "World") -> List[Event]:
        """Process expired dilemmas with auto-choice"""
        events = []

        for dilemma in list(self.pending_dilemmas.values()):
            if dilemma.status != "pending":
                continue

            if dilemma.expires_at_year and world.year >= dilemma.expires_at_year:
                country = world.countries.get(dilemma.country_id)
                if not country:
                    continue

                if dilemma.auto_choice:
                    # Auto-resolve with default choice
                    result = self.resolve_dilemma(
                        dilemma.id, dilemma.auto_choice, country, world
                    )
                    if result:
                        events.append(Event(
                            id=f"dilemma_expired_{world.year}_{dilemma.id}",
                            year=world.year,
                            type="dilemma_expired",
                            title="Dilemma Expired",
                            title_fr="Dilemme expire",
                            description=f"{dilemma.title} expired with default choice",
                            description_fr=f"{dilemma.title_fr} expire avec le choix par defaut",
                            country_id=country.id
                        ))
                else:
                    # Just expire without resolution
                    dilemma.status = "expired"
                    events.append(Event(
                        id=f"dilemma_expired_{world.year}_{dilemma.id}",
                        year=world.year,
                        type="dilemma_expired",
                        title="Dilemma Expired",
                        title_fr="Dilemme expire",
                        description=f"{dilemma.title} expired without resolution",
                        description_fr=f"{dilemma.title_fr} expire sans resolution",
                        country_id=country.id
                    ))

        return events


# Global dilemma manager instance
dilemma_manager = DilemmaManager()
