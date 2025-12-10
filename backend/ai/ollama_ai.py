"""Ollama LLM integration for Historia Lite AI decisions"""
import logging
import httpx
import json
from typing import Optional, Dict, Any, List

from config import settings
from engine.country import Country
from engine.world import World
from engine.events import Event

logger = logging.getLogger(__name__)


class OllamaAI:
    """AI decision making using Ollama LLM"""

    def __init__(
        self,
        base_url: str = settings.ollama_url,
        model: str = settings.ollama_model,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = settings.ollama_timeout

    async def is_available(self) -> bool:
        """Check if Ollama is available"""
        return await self.check_connection()

    async def check_connection(self) -> bool:
        """Check if Ollama server is reachable"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except httpx.ConnectError as e:
            logger.warning(f"Ollama connection refused: {e}")
            return False
        except httpx.TimeoutException:
            logger.warning("Ollama connection timeout")
            return False
        except httpx.HTTPError as e:
            logger.warning(f"Ollama HTTP error: {e}")
            return False

    async def list_models(self) -> List[str]:
        """List available models on Ollama server"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except httpx.ConnectError as e:
            logger.warning(f"Cannot list Ollama models - connection refused: {e}")
        except httpx.TimeoutException:
            logger.warning("Cannot list Ollama models - timeout")
        except httpx.HTTPError as e:
            logger.warning(f"Cannot list Ollama models - HTTP error: {e}")
        return []

    async def make_decision(
        self, country: Country, world: World
    ) -> Optional[Dict[str, Any]]:
        """Ask Ollama to make a decision for a country"""

        # Build context prompt
        prompt = self._build_prompt(country, world)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 300,
                        },
                    },
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    logger.error(f"Ollama error: {response.status_code}")
                    return None

                result = response.json()
                return self._parse_response(result.get("response", ""), country, world)

        except httpx.TimeoutException:
            logger.warning(f"Ollama timeout for {country.id}")
            return None
        except httpx.ConnectError as e:
            logger.error(f"Ollama connection refused for {country.id}: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error for {country.id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ollama response parse error for {country.id}: {e}")
            return None

    def _build_prompt(self, country: Country, world: World) -> str:
        """Build the decision prompt for Ollama"""

        # Get relevant neighbors and rivals
        rivals_info = []
        for rival_id in country.rivals[:3]:
            rival = world.get_country(rival_id)
            if rival:
                rivals_info.append(
                    f"- {rival.name_fr}: Eco {rival.economy}, Mil {rival.military}, "
                    f"Nuc {rival.nuclear}, Relations: {country.get_relation(rival_id)}"
                )

        allies_info = []
        for ally_id in country.allies[:3]:
            ally = world.get_country(ally_id)
            if ally:
                allies_info.append(f"- {ally.name_fr}")

        # Active conflicts
        conflicts_info = ""
        if country.at_war:
            enemies = [world.get_country(e) for e in country.at_war]
            enemies_names = [e.name_fr for e in enemies if e]
            conflicts_info = f"\nEN GUERRE AVEC: {', '.join(enemies_names)}"

        # Sanctions
        sanctions_info = ""
        if country.sanctions_on:
            sanctions_info = f"\nSanctions actives contre: {', '.join(country.sanctions_on)}"

        # Build the prompt
        prompt = f"""Tu es le dirigeant de {country.name_fr} en {world.year}.

SITUATION DE TON PAYS:
- Population: {country.population}/100
- Economie: {country.economy}/100
- Militaire: {country.military}/100
- Nucleaire: {country.nuclear}/100
- Technologie: {country.technology}/100
- Stabilite: {country.stability}/100
- Soft Power: {country.soft_power}/100
- Ressources: {country.resources}/100
- Regime: {country.regime}
- Blocs: {', '.join(country.blocs) if country.blocs else 'Aucun'}
{conflicts_info}
{sanctions_info}

ALLIES: {', '.join(allies_info) if allies_info else 'Aucun'}

RIVAUX:
{chr(10).join(rivals_info) if rivals_info else 'Aucun rival majeur'}

CONTEXTE MONDIAL:
- Prix du petrole: {world.oil_price}$/baril
- Tension mondiale: {world.global_tension}/100
- Annee: {world.year}

ACTIONS POSSIBLES:
1. ECONOMIE - Developper l'economie (+3 eco)
2. MILITAIRE - Renforcer l'armee (+3 mil, -1 eco)
3. TECHNOLOGIE - Investir en R&D (+3 tech, -2 eco)
4. STABILITE - Renforcer la stabilite (+5 stab)
5. INFLUENCE - Etendre l'influence mondiale (+3 soft power)
6. SANCTIONS - Imposer des sanctions a un rival
7. ALLIANCE - Proposer une alliance
8. NUCLEAIRE - Developper le programme nucleaire (+5 nuc, -10 soft power)
9. RIEN - Maintenir le statu quo

Reponds UNIQUEMENT avec ce format JSON:
{{"action": "NOM_ACTION", "cible": "CODE_PAYS_SI_APPLICABLE", "raison": "explication courte"}}

Exemple: {{"action": "SANCTIONS", "cible": "USA", "raison": "Represailles contre les sanctions americaines"}}
Exemple: {{"action": "ECONOMIE", "cible": null, "raison": "L'economie doit etre prioritaire"}}

Ta decision:"""

        return prompt

    def _parse_response(
        self, response: str, country: Country, world: World
    ) -> Optional[Dict[str, Any]]:
        """Parse Ollama response into a decision"""

        try:
            # Try to extract JSON from response
            response = response.strip()

            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON found in response: {response[:100]}")
                return None

            json_str = response[start:end]
            decision = json.loads(json_str)

            # Validate action
            valid_actions = [
                "ECONOMIE", "MILITAIRE", "TECHNOLOGIE", "STABILITE",
                "INFLUENCE", "SANCTIONS", "ALLIANCE", "NUCLEAIRE", "RIEN"
            ]

            action = decision.get("action", "").upper()
            if action not in valid_actions:
                logger.warning(f"Invalid action: {action}")
                return None

            return {
                "action": action,
                "target": decision.get("cible"),
                "reason": decision.get("raison", ""),
                "raw_response": response,
            }

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}, response: {response[:100]}")
            return None


def execute_ollama_decision(
    country: Country, world: World, decision: Dict[str, Any]
) -> Optional[Event]:
    """Execute a decision made by Ollama"""

    action = decision.get("action", "RIEN")
    target_id = decision.get("target")
    reason = decision.get("reason", "")

    if action == "ECONOMIE":
        country.economy = min(100, country.economy + 3)
        return _create_event(
            world, country, "decision",
            "Developpement economique",
            f"{country.name_fr} investit dans son economie. {reason}",
        )

    elif action == "MILITAIRE":
        country.military = min(100, country.military + 3)
        country.economy = max(0, country.economy - 1)
        return _create_event(
            world, country, "decision",
            "Renforcement militaire",
            f"{country.name_fr} renforce ses forces armees. {reason}",
        )

    elif action == "TECHNOLOGIE":
        country.technology = min(100, country.technology + 3)
        country.economy = max(0, country.economy - 2)
        return _create_event(
            world, country, "decision",
            "Investissement technologique",
            f"{country.name_fr} investit massivement en R&D. {reason}",
        )

    elif action == "STABILITE":
        country.stability = min(100, country.stability + 5)
        return _create_event(
            world, country, "decision",
            "Mesures de stabilite",
            f"{country.name_fr} renforce sa stabilite interne. {reason}",
        )

    elif action == "INFLUENCE":
        country.soft_power = min(100, country.soft_power + 3)
        return _create_event(
            world, country, "decision",
            "Expansion d'influence",
            f"{country.name_fr} etend son influence mondiale. {reason}",
        )

    elif action == "SANCTIONS":
        if target_id:
            target = world.get_country(target_id.upper())
            if target and target_id not in country.sanctions_on:
                country.sanctions_on.append(target_id.upper())
                country.modify_relation(target_id.upper(), -20)
                target.modify_relation(country.id, -20)
                return _create_event(
                    world, country, "sanctions",
                    f"Sanctions contre {target.name_fr}",
                    f"{country.name_fr} impose des sanctions a {target.name_fr}. {reason}",
                    target_id=target_id.upper(),
                )

    elif action == "ALLIANCE":
        if target_id:
            ally = world.get_country(target_id.upper())
            if ally and target_id.upper() not in country.allies:
                # Check if ally accepts (based on relations)
                if country.get_relation(target_id.upper()) > -20:
                    country.allies.append(target_id.upper())
                    ally.allies.append(country.id)
                    country.modify_relation(target_id.upper(), 15)
                    ally.modify_relation(country.id, 15)
                    return _create_event(
                        world, country, "diplomacy",
                        f"Alliance avec {ally.name_fr}",
                        f"{country.name_fr} forme une alliance avec {ally.name_fr}. {reason}",
                        target_id=target_id.upper(),
                    )

    elif action == "NUCLEAIRE":
        if country.technology >= 50:  # Need tech to develop nukes
            country.nuclear = min(100, country.nuclear + 5)
            country.soft_power = max(0, country.soft_power - 10)
            # Negative reaction from others
            for power in world.get_superpowers():
                if power.id != country.id:
                    power.modify_relation(country.id, -15)
            return _create_event(
                world, country, "military",
                "Programme nucleaire",
                f"{country.name_fr} avance son programme nucleaire. {reason}",
            )

    # RIEN or invalid action
    return None


def _create_event(
    world: World,
    country: Country,
    event_type: str,
    title: str,
    description: str,
    target_id: Optional[str] = None,
) -> Event:
    """Create an event from Ollama decision"""
    return Event(
        id=f"ollama_{world.year}_{country.id}_{event_type}",
        year=world.year,
        type=event_type,
        title=title,
        title_fr=title,
        description=description,
        description_fr=description,
        country_id=country.id,
        target_id=target_id,
    )
