"""Command interpreter for natural language player commands"""
import json
import logging
import re
import uuid
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import httpx

from schemas.interaction import (
    CommandAction,
    CommandCategory,
    CommandCost,
    CommandInterpretation,
    CommandResponse,
)
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)

# Country name mappings for command parsing
COUNTRY_ALIASES = {
    # French names
    "etats-unis": "USA", "etats unis": "USA", "usa": "USA", "amerique": "USA",
    "chine": "CHN", "china": "CHN",
    "russie": "RUS", "russia": "RUS",
    "france": "FRA",
    "allemagne": "DEU", "germany": "DEU",
    "royaume-uni": "GBR", "uk": "GBR", "angleterre": "GBR", "britain": "GBR",
    "japon": "JPN", "japan": "JPN",
    "inde": "IND", "india": "IND",
    "bresil": "BRA", "brazil": "BRA",
    "italie": "ITA", "italy": "ITA",
    "espagne": "ESP", "spain": "ESP",
    "pologne": "POL", "poland": "POL",
    "ukraine": "UKR",
    "iran": "IRN",
    "israel": "ISR",
    "turquie": "TUR", "turkey": "TUR",
    "arabie saoudite": "SAU", "saudi": "SAU",
    "belgique": "BEL", "belgium": "BEL",
    "pays-bas": "NLD", "netherlands": "NLD", "hollande": "NLD",
    "suede": "SWE", "sweden": "SWE",
    "coree du sud": "KOR", "south korea": "KOR",
    "coree du nord": "PRK", "north korea": "PRK",
    "taiwan": "TWN",
    "australie": "AUS", "australia": "AUS",
    "canada": "CAN",
    "mexique": "MEX", "mexico": "MEX",
    "argentine": "ARG", "argentina": "ARG",
}

# Project name mappings
PROJECT_ALIASES = {
    "programme spatial": "space_program",
    "programme mars": "mars_program",
    "space program": "space_program",
    "mars program": "mars_program",
    "programme nucleaire": "nuclear_program",
    "nuclear program": "nuclear_program",
    "modernisation militaire": "military_modernization",
    "military modernization": "military_modernization",
    "reforme economique": "economic_reform",
    "economic reform": "economic_reform",
    "infrastructure": "infrastructure",
    "ia": "ai_research",
    "intelligence artificielle": "ai_research",
    "ai research": "ai_research",
}


class CommandInterpreter:
    """Interprets natural language commands from players"""

    SYSTEM_PROMPT = """Tu es l'assistant strategique du pays {country_name}.
Analyse la commande du joueur et retourne UNIQUEMENT un JSON valide (sans texte avant/apres).

Types d'actions possibles:
- military: attack, defend, mobilize, demobilize
- diplomatic: propose_alliance, declare_war, peace_offer, sanctions, lift_sanctions
- economic: tax_increase, tax_decrease, invest, embargo
- project: start_project, cancel_project, accelerate_project
- internal: reform, propaganda, suppress, election

Contexte actuel:
- Economie: {economy}/100
- Militaire: {military}/100
- Stabilite: {stability}/100
- En guerre avec: {at_war}
- Allies: {allies}
- Projets en cours: {active_projects}

Format de reponse JSON:
{{
    "category": "military|diplomatic|economic|project|internal",
    "action": "nom_action",
    "target_country_id": "XXX" ou null,
    "target_project_id": "xxx_xxx" ou null,
    "parameters": {{}},
    "confidence": 0.0-1.0
}}

Commande a analyser: "{command}"
"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.pending_commands: Dict[str, CommandResponse] = {}

    async def interpret(
        self,
        command: str,
        country: "Country",
        world: "World",
        use_ollama: bool = True
    ) -> CommandResponse:
        """Interpret a natural language command"""
        command_id = str(uuid.uuid4())[:8]

        # Try Ollama first if available
        if use_ollama:
            interpretation = await self._interpret_with_ollama(command, country, world)
        else:
            interpretation = None

        # Fallback to algorithmic interpretation
        if interpretation is None:
            interpretation = self._interpret_algorithmic(command, country, world)

        # Validate feasibility
        feasible, reason = self._validate_feasibility(interpretation, country, world)

        # Calculate costs
        cost = self._calculate_cost(interpretation, country)

        # Generate confirmation message
        confirm_msg, confirm_msg_fr = self._generate_confirmation(
            interpretation, country, world, cost
        )

        response = CommandResponse(
            command_id=command_id,
            original_command=command,
            interpreted_as=f"{interpretation.category.value}:{interpretation.action.value}",
            interpretation=interpretation,
            feasible=feasible,
            feasibility_reason=reason if not feasible else None,
            cost=cost,
            requires_confirmation=True,
            confirmation_message=confirm_msg,
            confirmation_message_fr=confirm_msg_fr,
            executed=False,
        )

        # Store for later confirmation
        self.pending_commands[command_id] = response
        return response

    async def _interpret_with_ollama(
        self,
        command: str,
        country: "Country",
        world: "World"
    ) -> Optional[CommandInterpretation]:
        """Use Ollama to interpret the command"""
        try:
            prompt = self.SYSTEM_PROMPT.format(
                country_name=country.name_fr,
                economy=country.economy,
                military=country.military,
                stability=country.stability,
                at_war=", ".join(country.at_war) if country.at_war else "personne",
                allies=", ".join(country.allies) if country.allies else "aucun",
                active_projects="aucun",  # TODO: integrate projects
                command=command
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3}
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    text = result.get("response", "")

                    # Extract JSON from response
                    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        return CommandInterpretation(
                            category=CommandCategory(data.get("category", "military")),
                            action=CommandAction(data.get("action", "attack")),
                            target_country_id=data.get("target_country_id"),
                            target_project_id=data.get("target_project_id"),
                            parameters=data.get("parameters", {}),
                            confidence=data.get("confidence", 0.8)
                        )
        except Exception as e:
            logger.warning(f"Ollama interpretation failed: {e}")

        return None

    def _interpret_algorithmic(
        self,
        command: str,
        country: "Country",
        world: "World"
    ) -> CommandInterpretation:
        """Fallback algorithmic interpretation"""
        cmd_lower = command.lower()

        # Detect target country
        target = self._extract_country(cmd_lower, world)

        # Detect project
        project = self._extract_project(cmd_lower)

        # Military commands
        if any(w in cmd_lower for w in ["attaque", "attack", "envahi", "invade"]):
            return CommandInterpretation(
                category=CommandCategory.MILITARY,
                action=CommandAction.ATTACK,
                target_country_id=target,
                confidence=0.9 if target else 0.5
            )

        if any(w in cmd_lower for w in ["defend", "defense", "protege"]):
            return CommandInterpretation(
                category=CommandCategory.MILITARY,
                action=CommandAction.DEFEND,
                confidence=0.8
            )

        if any(w in cmd_lower for w in ["mobilise", "mobilize", "armee"]):
            return CommandInterpretation(
                category=CommandCategory.MILITARY,
                action=CommandAction.MOBILIZE,
                confidence=0.8
            )

        # Diplomatic commands
        if any(w in cmd_lower for w in ["alliance", "allie"]):
            return CommandInterpretation(
                category=CommandCategory.DIPLOMATIC,
                action=CommandAction.PROPOSE_ALLIANCE,
                target_country_id=target,
                confidence=0.9 if target else 0.5
            )

        if any(w in cmd_lower for w in ["guerre", "war", "declare"]):
            return CommandInterpretation(
                category=CommandCategory.DIPLOMATIC,
                action=CommandAction.DECLARE_WAR,
                target_country_id=target,
                confidence=0.9 if target else 0.5
            )

        if any(w in cmd_lower for w in ["paix", "peace", "armistice"]):
            return CommandInterpretation(
                category=CommandCategory.DIPLOMATIC,
                action=CommandAction.PEACE_OFFER,
                target_country_id=target,
                confidence=0.8
            )

        if any(w in cmd_lower for w in ["sanction", "embargo"]):
            if any(w in cmd_lower for w in ["leve", "retire", "lift", "remove"]):
                return CommandInterpretation(
                    category=CommandCategory.DIPLOMATIC,
                    action=CommandAction.LIFT_SANCTIONS,
                    target_country_id=target,
                    confidence=0.8
                )
            return CommandInterpretation(
                category=CommandCategory.DIPLOMATIC,
                action=CommandAction.SANCTIONS,
                target_country_id=target,
                confidence=0.8
            )

        # Economic commands
        if any(w in cmd_lower for w in ["impot", "taxe", "tax"]):
            if any(w in cmd_lower for w in ["augmente", "increase", "hausse"]):
                return CommandInterpretation(
                    category=CommandCategory.ECONOMIC,
                    action=CommandAction.TAX_INCREASE,
                    confidence=0.9
                )
            if any(w in cmd_lower for w in ["baisse", "diminue", "decrease", "reduce"]):
                return CommandInterpretation(
                    category=CommandCategory.ECONOMIC,
                    action=CommandAction.TAX_DECREASE,
                    confidence=0.9
                )

        if any(w in cmd_lower for w in ["investi", "invest"]):
            return CommandInterpretation(
                category=CommandCategory.ECONOMIC,
                action=CommandAction.INVEST,
                target_country_id=target,
                confidence=0.7
            )

        # Project commands
        if any(w in cmd_lower for w in ["programme", "project", "lance", "cree", "start"]):
            return CommandInterpretation(
                category=CommandCategory.PROJECT,
                action=CommandAction.START_PROJECT,
                target_project_id=project,
                confidence=0.8 if project else 0.5
            )

        if any(w in cmd_lower for w in ["annule", "cancel", "arrete", "stop"]):
            return CommandInterpretation(
                category=CommandCategory.PROJECT,
                action=CommandAction.CANCEL_PROJECT,
                target_project_id=project,
                confidence=0.7
            )

        if any(w in cmd_lower for w in ["accelere", "accelerate", "priorite"]):
            return CommandInterpretation(
                category=CommandCategory.PROJECT,
                action=CommandAction.ACCELERATE_PROJECT,
                target_project_id=project,
                confidence=0.7
            )

        # Internal commands
        if any(w in cmd_lower for w in ["reforme", "reform"]):
            return CommandInterpretation(
                category=CommandCategory.INTERNAL,
                action=CommandAction.REFORM,
                confidence=0.7
            )

        if any(w in cmd_lower for w in ["propagande", "propaganda"]):
            return CommandInterpretation(
                category=CommandCategory.INTERNAL,
                action=CommandAction.PROPAGANDA,
                confidence=0.7
            )

        if any(w in cmd_lower for w in ["reprime", "suppress", "repression"]):
            return CommandInterpretation(
                category=CommandCategory.INTERNAL,
                action=CommandAction.SUPPRESS,
                confidence=0.7
            )

        if any(w in cmd_lower for w in ["election", "vote"]):
            return CommandInterpretation(
                category=CommandCategory.INTERNAL,
                action=CommandAction.ELECTION,
                confidence=0.7
            )

        # Default: unclear command
        return CommandInterpretation(
            category=CommandCategory.INTERNAL,
            action=CommandAction.REFORM,
            confidence=0.3,
            parameters={"unclear": True}
        )

    def _extract_country(self, command: str, world: "World") -> Optional[str]:
        """Extract country ID from command text"""
        for alias, country_id in COUNTRY_ALIASES.items():
            if alias in command:
                return country_id

        # Also check actual country IDs
        for country_id in world.countries.keys():
            if country_id.lower() in command:
                return country_id

        return None

    def _extract_project(self, command: str) -> Optional[str]:
        """Extract project ID from command text"""
        for alias, project_id in PROJECT_ALIASES.items():
            if alias in command:
                return project_id
        return None

    def _validate_feasibility(
        self,
        interpretation: CommandInterpretation,
        country: "Country",
        world: "World"
    ) -> Tuple[bool, Optional[str]]:
        """Check if the command can be executed"""
        action = interpretation.action
        target = interpretation.target_country_id

        # Attack requires target and sufficient military
        if action == CommandAction.ATTACK:
            if not target:
                return False, "No target country specified"
            if country.military < 20:
                return False, "Insufficient military strength"
            target_country = world.get_country(target)
            if target_country and target_country.nuclear > 50 and country.nuclear < 50:
                return False, "Cannot attack nuclear power without nuclear deterrent"

        # Alliance requires target not at war
        if action == CommandAction.PROPOSE_ALLIANCE:
            if not target:
                return False, "No target country specified"
            if target in country.at_war:
                return False, "Cannot ally with country at war"
            if target in country.rivals:
                return False, "Cannot ally with rival"

        # Sanctions require target
        if action == CommandAction.SANCTIONS:
            if not target:
                return False, "No target country specified"
            if target in country.allies:
                return False, "Cannot sanction ally"

        # Tax increase requires minimum stability
        if action == CommandAction.TAX_INCREASE:
            if country.stability < 30:
                return False, "Stability too low for tax increase"

        # Projects require minimum technology
        if action == CommandAction.START_PROJECT:
            project_id = interpretation.target_project_id
            if project_id in ["nuclear_program", "mars_program"]:
                if country.technology < 50:
                    return False, "Insufficient technology level"

        return True, None

    def _calculate_cost(
        self,
        interpretation: CommandInterpretation,
        country: "Country"
    ) -> CommandCost:
        """Calculate resource costs for the command"""
        action = interpretation.action

        costs = {
            CommandAction.ATTACK: CommandCost(military=-15, economy=-10, stability=-5),
            CommandAction.DEFEND: CommandCost(military=-5, economy=-3),
            CommandAction.MOBILIZE: CommandCost(economy=-5, stability=-3),
            CommandAction.DEMOBILIZE: CommandCost(stability=+5),
            CommandAction.DECLARE_WAR: CommandCost(stability=-10, soft_power=-15),
            CommandAction.PROPOSE_ALLIANCE: CommandCost(soft_power=-2),
            CommandAction.PEACE_OFFER: CommandCost(soft_power=+5),
            CommandAction.SANCTIONS: CommandCost(economy=-3, soft_power=-5),
            CommandAction.LIFT_SANCTIONS: CommandCost(soft_power=+3),
            CommandAction.TAX_INCREASE: CommandCost(economy=+10, stability=-8),
            CommandAction.TAX_DECREASE: CommandCost(economy=-10, stability=+5),
            CommandAction.INVEST: CommandCost(economy=-10, technology=+3),
            CommandAction.EMBARGO: CommandCost(economy=-5),
            CommandAction.START_PROJECT: CommandCost(economy=-5),
            CommandAction.CANCEL_PROJECT: CommandCost(stability=-3),
            CommandAction.ACCELERATE_PROJECT: CommandCost(economy=-8),
            CommandAction.REFORM: CommandCost(stability=-5, economy=+5),
            CommandAction.PROPAGANDA: CommandCost(economy=-3, stability=+5),
            CommandAction.SUPPRESS: CommandCost(stability=-10, soft_power=-10),
            CommandAction.ELECTION: CommandCost(stability=-5),
        }

        return costs.get(action, CommandCost())

    def _generate_confirmation(
        self,
        interpretation: CommandInterpretation,
        country: "Country",
        world: "World",
        cost: CommandCost
    ) -> Tuple[str, str]:
        """Generate confirmation message for the command"""
        action = interpretation.action
        target = interpretation.target_country_id
        target_name = ""

        if target:
            target_country = world.get_country(target)
            if target_country:
                target_name = target_country.name

        messages = {
            CommandAction.ATTACK: (
                f"Attack {target_name}? This will cost {abs(cost.military)} military, "
                f"{abs(cost.economy)} economy. War will begin.",
                f"Attaquer {target_name}? Cela coutera {abs(cost.military)} militaire, "
                f"{abs(cost.economy)} economie. La guerre commencera."
            ),
            CommandAction.DECLARE_WAR: (
                f"Declare war on {target_name}? Relations will be severed.",
                f"Declarer la guerre a {target_name}? Les relations seront rompues."
            ),
            CommandAction.PROPOSE_ALLIANCE: (
                f"Propose alliance to {target_name}? They may accept or refuse.",
                f"Proposer une alliance a {target_name}? Ils peuvent accepter ou refuser."
            ),
            CommandAction.SANCTIONS: (
                f"Impose sanctions on {target_name}? This will hurt both economies.",
                f"Imposer des sanctions a {target_name}? Cela nuira aux deux economies."
            ),
            CommandAction.TAX_INCREASE: (
                f"Increase taxes? Economy +{cost.economy}, Stability {cost.stability}",
                f"Augmenter les impots? Economie +{cost.economy}, Stabilite {cost.stability}"
            ),
            CommandAction.TAX_DECREASE: (
                f"Decrease taxes? Economy {cost.economy}, Stability +{abs(cost.stability)}",
                f"Baisser les impots? Economie {cost.economy}, Stabilite +{abs(cost.stability)}"
            ),
            CommandAction.START_PROJECT: (
                f"Start project {interpretation.target_project_id}? Annual cost: {abs(cost.economy)} economy",
                f"Demarrer le projet {interpretation.target_project_id}? Cout annuel: {abs(cost.economy)} economie"
            ),
        }

        default = (
            f"Execute {action.value}? Confirm to proceed.",
            f"Executer {action.value}? Confirmez pour continuer."
        )

        return messages.get(action, default)

    async def execute(
        self,
        command_id: str,
        world: "World"
    ) -> Tuple[bool, List[Event]]:
        """Execute a confirmed command"""
        if command_id not in self.pending_commands:
            return False, []

        response = self.pending_commands[command_id]
        if not response.feasible:
            return False, []

        interpretation = response.interpretation
        country = world.get_country(response.interpretation.parameters.get("player_id", "USA"))
        if not country:
            return False, []

        events = []
        action = interpretation.action
        target_id = interpretation.target_country_id

        # Apply costs
        cost = response.cost
        country.economy = max(0, min(100, country.economy + cost.economy))
        country.military = max(0, min(100, country.military + cost.military))
        country.stability = max(0, min(100, country.stability + cost.stability))
        country.soft_power = max(0, min(100, country.soft_power + cost.soft_power))
        country.technology = max(0, min(100, country.technology + cost.technology))

        # Execute action-specific logic
        if action == CommandAction.ATTACK and target_id:
            if target_id not in country.at_war:
                country.at_war.append(target_id)
            target = world.get_country(target_id)
            if target and country.id not in target.at_war:
                target.at_war.append(country.id)

            events.append(Event(
                id=f"war_{world.year}_{country.id}_{target_id}",
                year=world.year,
                type="military",
                title="War Declared",
                title_fr="Guerre declaree",
                description=f"{country.name} attacks {target.name if target else target_id}",
                description_fr=f"{country.name_fr} attaque {target.name_fr if target else target_id}",
                country_id=country.id,
                target_id=target_id
            ))

        elif action == CommandAction.DECLARE_WAR and target_id:
            if target_id not in country.at_war:
                country.at_war.append(target_id)
            target = world.get_country(target_id)
            if target and country.id not in target.at_war:
                target.at_war.append(country.id)
            country.modify_relation(target_id, -50)

            events.append(Event(
                id=f"declare_war_{world.year}_{country.id}_{target_id}",
                year=world.year,
                type="diplomatic",
                title="War Declaration",
                title_fr="Declaration de guerre",
                description=f"{country.name} declares war on {target.name if target else target_id}",
                description_fr=f"{country.name_fr} declare la guerre a {target.name_fr if target else target_id}",
                country_id=country.id,
                target_id=target_id
            ))

        elif action == CommandAction.PROPOSE_ALLIANCE and target_id:
            # Alliance proposal - will be handled by dialogue system
            events.append(Event(
                id=f"alliance_proposal_{world.year}_{country.id}_{target_id}",
                year=world.year,
                type="diplomatic",
                title="Alliance Proposed",
                title_fr="Alliance proposee",
                description=f"{country.name} proposes alliance to {target_id}",
                description_fr=f"{country.name_fr} propose une alliance a {target_id}",
                country_id=country.id,
                target_id=target_id
            ))

        elif action == CommandAction.SANCTIONS and target_id:
            if target_id not in country.sanctions_on:
                country.sanctions_on.append(target_id)
            country.modify_relation(target_id, -20)

            events.append(Event(
                id=f"sanctions_{world.year}_{country.id}_{target_id}",
                year=world.year,
                type="sanctions",
                title="Sanctions Imposed",
                title_fr="Sanctions imposees",
                description=f"{country.name} imposes sanctions on {target_id}",
                description_fr=f"{country.name_fr} impose des sanctions a {target_id}",
                country_id=country.id,
                target_id=target_id
            ))

        elif action == CommandAction.LIFT_SANCTIONS and target_id:
            if target_id in country.sanctions_on:
                country.sanctions_on.remove(target_id)
            country.modify_relation(target_id, +10)

            events.append(Event(
                id=f"lift_sanctions_{world.year}_{country.id}_{target_id}",
                year=world.year,
                type="diplomatic",
                title="Sanctions Lifted",
                title_fr="Sanctions levees",
                description=f"{country.name} lifts sanctions on {target_id}",
                description_fr=f"{country.name_fr} leve les sanctions contre {target_id}",
                country_id=country.id,
                target_id=target_id
            ))

        elif action in [CommandAction.TAX_INCREASE, CommandAction.TAX_DECREASE]:
            event_type = "economic"
            title = "Tax Policy Change"
            title_fr = "Changement de politique fiscale"
            events.append(Event(
                id=f"tax_{world.year}_{country.id}",
                year=world.year,
                type=event_type,
                title=title,
                title_fr=title_fr,
                description=f"{country.name} changes tax policy",
                description_fr=f"{country.name_fr} change sa politique fiscale",
                country_id=country.id
            ))

        # Mark as executed
        response.executed = True
        response.events = [{"id": e.id, "type": e.type, "title": e.title} for e in events]

        # Remove from pending
        del self.pending_commands[command_id]

        logger.info(f"Executed command {command_id}: {action.value}")
        return True, events

    def cancel(self, command_id: str) -> bool:
        """Cancel a pending command"""
        if command_id in self.pending_commands:
            del self.pending_commands[command_id]
            return True
        return False
