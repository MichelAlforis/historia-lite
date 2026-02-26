"""Command interpreter for natural language player commands"""
import json
import logging
import random
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

        # Calculate costs (dynamic based on target strength + random)
        cost = self._calculate_cost(interpretation, country, world)

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
        """Extract country ID from command text - searches all countries dynamically"""
        # Normalize command for matching
        cmd_normalized = self._normalize_text(command)

        # 1. First check hardcoded aliases (common variations)
        for alias, country_id in COUNTRY_ALIASES.items():
            if alias in cmd_normalized:
                return country_id

        # 2. Search in ALL countries from world data (dynamic)
        for country_id, country in world.countries.items():
            # Check country ID (e.g., "PRT", "USA")
            if country_id.lower() in cmd_normalized:
                return country_id

            # Check English name (e.g., "Portugal", "Germany")
            if hasattr(country, 'name') and country.name:
                name_normalized = self._normalize_text(country.name)
                if name_normalized in cmd_normalized:
                    return country_id

            # Check French name (e.g., "Portugal", "Allemagne")
            if hasattr(country, 'name_fr') and country.name_fr:
                name_fr_normalized = self._normalize_text(country.name_fr)
                if name_fr_normalized in cmd_normalized:
                    return country_id

        return None

    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching - remove accents, lowercase"""
        import unicodedata
        # Lowercase
        text = text.lower()
        # Remove accents (é -> e, ç -> c, etc.)
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text

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
        country: "Country",
        world: "World" = None
    ) -> CommandCost:
        """Calculate dynamic resource costs based on target strength + random factor"""
        action = interpretation.action
        target_id = interpretation.target_country_id

        # Get target country strength for comparison
        target_military = 50  # default
        target_economy = 50
        target_tier = 3  # medium power by default

        if target_id and world:
            # Use get_any_country to find Tier 4-6 countries too
            target = world.get_any_country(target_id)
            if target:
                target_military = getattr(target, 'military', 20)  # Lower default for minor countries
                target_economy = getattr(target, 'economy', 30)
                target_tier = getattr(target, 'tier', 4)  # Default to Tier 4 for minor countries

        # Calculate difficulty modifier based on target strength
        # Stronger targets = higher costs, weaker targets = lower costs
        # Range: 0.5 (very weak target) to 1.5 (very strong target)
        difficulty = max(0.5, min(1.5, target_military / max(20, country.military) + 0.5))

        # Tier modifier: Tier 1 = 1.3x, Tier 4+ = 0.7x
        tier_modifier = {1: 1.3, 2: 1.1, 3: 1.0, 4: 0.7, 5: 0.6, 6: 0.5}.get(target_tier, 0.8)

        # Random factor: +/- 15% variation
        random_factor = random.uniform(0.85, 1.15)

        def dynamic_cost(base: int, uses_strength: bool = True) -> int:
            """Apply modifiers to base cost"""
            if uses_strength:
                # Cap total multiplier to avoid extreme costs
                total_mult = min(2.0, difficulty * tier_modifier * random_factor)
                modified = base * total_mult
            else:
                modified = base * random_factor
            return int(round(modified))

        # Base costs with dynamic calculation
        if action == CommandAction.ATTACK:
            return CommandCost(
                military=-dynamic_cost(15, True),
                economy=-dynamic_cost(10, True),
                stability=-dynamic_cost(5, False)
            )
        elif action == CommandAction.DEFEND:
            return CommandCost(military=-dynamic_cost(5, False), economy=-dynamic_cost(3, False))
        elif action == CommandAction.MOBILIZE:
            return CommandCost(economy=-dynamic_cost(5, False), stability=-dynamic_cost(3, False))
        elif action == CommandAction.DEMOBILIZE:
            return CommandCost(stability=dynamic_cost(5, False))
        elif action == CommandAction.DECLARE_WAR:
            return CommandCost(
                stability=-dynamic_cost(10, True),
                soft_power=-dynamic_cost(15, True)
            )
        elif action == CommandAction.PROPOSE_ALLIANCE:
            return CommandCost(soft_power=-dynamic_cost(2, False))
        elif action == CommandAction.PEACE_OFFER:
            return CommandCost(soft_power=dynamic_cost(5, False))
        elif action == CommandAction.SANCTIONS:
            # Sanctioning a stronger economy costs more
            eco_ratio = target_economy / max(10, country.economy)
            return CommandCost(
                economy=-int(round(3 * eco_ratio * random_factor)),
                soft_power=-dynamic_cost(5, False)
            )
        elif action == CommandAction.LIFT_SANCTIONS:
            return CommandCost(soft_power=dynamic_cost(3, False))
        elif action == CommandAction.TAX_INCREASE:
            return CommandCost(economy=dynamic_cost(10, False), stability=-dynamic_cost(8, False))
        elif action == CommandAction.TAX_DECREASE:
            return CommandCost(economy=-dynamic_cost(10, False), stability=dynamic_cost(5, False))
        elif action == CommandAction.INVEST:
            return CommandCost(economy=-dynamic_cost(10, False), technology=dynamic_cost(3, False))
        elif action == CommandAction.EMBARGO:
            return CommandCost(economy=-dynamic_cost(5, False))
        elif action == CommandAction.START_PROJECT:
            return CommandCost(economy=-dynamic_cost(5, False))
        elif action == CommandAction.CANCEL_PROJECT:
            return CommandCost(stability=-dynamic_cost(3, False))
        elif action == CommandAction.ACCELERATE_PROJECT:
            return CommandCost(economy=-dynamic_cost(8, False))
        elif action == CommandAction.REFORM:
            return CommandCost(stability=-dynamic_cost(5, False), economy=dynamic_cost(5, False))
        elif action == CommandAction.PROPAGANDA:
            return CommandCost(economy=-dynamic_cost(3, False), stability=dynamic_cost(5, False))
        elif action == CommandAction.SUPPRESS:
            return CommandCost(stability=-dynamic_cost(10, False), soft_power=-dynamic_cost(10, False))
        elif action == CommandAction.ELECTION:
            return CommandCost(stability=-dynamic_cost(5, False))

        return CommandCost()

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
            # Use get_any_country to find countries in all tiers (1-6)
            target = world.get_any_country(target_id)
            if not target:
                return False, []

            # COMBAT RESOLUTION
            # Calculate combat power with random factor
            attacker_power = country.military * random.uniform(0.8, 1.2)
            target_military = getattr(target, 'military', 20)  # Default for Tier 4-6
            defender_power = target_military * random.uniform(0.7, 1.1)  # Slight defender disadvantage

            # Nuclear deterrence check (only for Tier 1-3 with nuclear attribute)
            target_nuclear = getattr(target, 'nuclear', 0)
            if target_nuclear > 50 and country.nuclear < 50:
                # Cannot conquer nuclear power without nukes
                events.append(Event(
                    id=f"attack_blocked_{world.year}_{country.id}_{target_id}",
                    year=world.year,
                    type="military",
                    title="Attack Repelled",
                    title_fr="Attaque repoussee",
                    description=f"{target.name}'s nuclear deterrence blocks {country.name}'s attack",
                    description_fr=f"La dissuasion nucleaire de {target.name_fr} bloque l'attaque de {country.name_fr}",
                    country_id=country.id,
                    target_id=target_id
                ))
                # War is declared but no conquest
                if target_id not in country.at_war:
                    country.at_war.append(target_id)
                if hasattr(target, 'at_war') and country.id not in target.at_war:
                    target.at_war.append(country.id)
            elif attacker_power > defender_power:
                # ATTACKER WINS - FULL ANNEXATION
                victory_margin = (attacker_power - defender_power) / max(defender_power, 1)

                # Apply losses to both sides
                attacker_losses = int(10 + random.randint(0, 10))
                defender_losses = int(15 + random.randint(5, 20))

                country.military = max(10, country.military - attacker_losses)

                # Get target resources BEFORE destroying them
                target_economy = getattr(target, 'economy', 30)
                target_population = getattr(target, 'population', 10)  # millions

                # Update target stats (handle both Tier 1-3 Country and Tier 4-6)
                if hasattr(target, 'military'):
                    target.military = max(0, target.military - defender_losses)
                if hasattr(target, 'stability'):
                    target.stability = max(0, target.stability - 30)
                if hasattr(target, 'economy'):
                    target.economy = max(5, target.economy - 20)

                # ===========================================
                # ANNEXATION: Target becomes part of attacker
                # ===========================================

                # 1. Add to sphere of influence (represents annexed territories)
                if target_id not in country.sphere_of_influence:
                    country.sphere_of_influence.append(target_id)

                # 2. Mark target as annexed
                if hasattr(target, 'under_influence_of'):
                    if isinstance(target.under_influence_of, dict):
                        target.under_influence_of = {country.id: 100}  # 100 = full annexation
                    else:
                        target.under_influence_of = country.id

                # 3. Target loses independence and sovereignty
                if hasattr(target, 'stability'):
                    target.stability = max(0, target.stability - 30)
                if hasattr(target, 'allies'):
                    target.allies = []  # No more independent alliances
                if hasattr(target, 'at_war'):
                    target.at_war = []  # Wars end with annexation

                # 4. ECONOMIC BENEFITS from annexation
                # Conqueror gains portion of target's economy (pillage + integration)
                economic_gain = int(target_economy * 0.3)  # 30% of target economy
                country.economy = min(100, country.economy + economic_gain)

                # 5. Population boost (more manpower)
                if hasattr(country, 'population') and target_population:
                    country.population += target_population

                # 6. Occupation cost: stability drops due to resistance
                occupation_cost = min(10, int(target_population / 5) + 3)
                country.stability = max(20, country.stability - occupation_cost)

                # 7. Remove from rivals/enemies lists
                if target_id in country.rivals:
                    country.rivals.remove(target_id)
                if target_id in country.at_war:
                    country.at_war.remove(target_id)

                target_name = getattr(target, 'name', target_id)
                target_name_fr = getattr(target, 'name_fr', target_name)

                events.append(Event(
                    id=f"annexation_{world.year}_{country.id}_{target_id}",
                    year=world.year,
                    type="military",
                    title="Territory Annexed",
                    title_fr="Territoire annexe",
                    description=f"{country.name} annexes {target_name}! Gained {economic_gain} economy. Occupation costs {occupation_cost} stability.",
                    description_fr=f"{country.name_fr} annexe {target_name_fr}! Gain de {economic_gain} en economie. L'occupation coute {occupation_cost} en stabilite.",
                    country_id=country.id,
                    target_id=target_id
                ))

                # 8. Global reaction - SEVERE diplomatic consequences
                # All countries lose trust (aggressor reputation)
                country.soft_power = max(0, country.soft_power - 15)

                # Allies especially upset
                for other_id in country.allies:
                    other = world.get_country(other_id)
                    if other and hasattr(other, 'modify_relation'):
                        other.modify_relation(country.id, -20)

                # World tension increases
                if hasattr(world, 'tension'):
                    world.tension = min(100, world.tension + 10)

            else:
                # DEFENDER WINS (or stalemate)
                attacker_losses = int(15 + random.randint(5, 15))
                defender_losses = int(5 + random.randint(0, 10))

                country.military = max(10, country.military - attacker_losses)
                country.stability = max(20, country.stability - 10)

                if hasattr(target, 'military'):
                    target.military = max(10, target.military - defender_losses)

                # War declared but attack repelled
                if target_id not in country.at_war:
                    country.at_war.append(target_id)
                if hasattr(target, 'at_war') and country.id not in target.at_war:
                    target.at_war.append(country.id)

                target_name = getattr(target, 'name', target_id)
                target_name_fr = getattr(target, 'name_fr', target_name)

                events.append(Event(
                    id=f"attack_failed_{world.year}_{country.id}_{target_id}",
                    year=world.year,
                    type="military",
                    title="Attack Failed",
                    title_fr="Attaque echouee",
                    description=f"{country.name}'s attack on {target_name} is repelled! War continues.",
                    description_fr=f"L'attaque de {country.name_fr} sur {target_name_fr} est repoussee! La guerre continue.",
                    country_id=country.id,
                    target_id=target_id
                ))

            # Relation drops to minimum (only for Tier 1-3 countries with modify_relation)
            if hasattr(country, 'modify_relation'):
                country.modify_relation(target_id, -100)

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
