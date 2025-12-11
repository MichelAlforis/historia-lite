"""AI-powered narrative event generator for Historia Lite - Phase 17+"""
import asyncio
import logging
import json
import random
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from config import settings
from engine.events import Event, EventEffect

logger = logging.getLogger(__name__)


class AIGeneratedEvent(BaseModel):
    """Structure for AI-generated narrative events"""
    title_fr: str
    description_fr: str
    event_type: str = "ai_narrative"
    effects: List[Dict[str, Any]] = Field(default_factory=list)
    severity: str = "normal"
    choices: Optional[List[Dict[str, str]]] = None


class AIEventGenerator:
    """Generate contextual narrative events using Ollama LLM"""

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
    ):
        self.base_url = base_url or settings.ollama_url
        self.model = model or "qwen2.5:7b"  # Use 7b for better narrative
        self.timeout = 30.0  # Longer timeout for narrative generation
        self.last_generated_year: Dict[str, int] = {}  # player_id -> year
        self.cooldown_years = 3  # Min years between AI events per player

    async def is_available(self) -> bool:
        """Check if Ollama is available for event generation"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
            return False

    def _should_generate(self, player_id: str, year: int) -> bool:
        """Check if we should generate an AI event (respects cooldown)"""
        last_year = self.last_generated_year.get(player_id, 0)
        return (year - last_year) >= self.cooldown_years

    def _build_world_context(self, world: Any, player: Any) -> str:
        """Build rich world context for the AI prompt"""
        # Current wars
        wars_text = ""
        active_wars = []
        for c in world.countries.values():
            if c.at_war:
                for enemy_id in c.at_war:
                    war_pair = tuple(sorted([c.id, enemy_id]))
                    if war_pair not in active_wars:
                        active_wars.append(war_pair)
                        enemy = world.get_country(enemy_id)
                        if enemy:
                            wars_text += f"- {c.name_fr} vs {enemy.name_fr}\n"

        # Recent events (last 3 years)
        recent_events = []
        for event in world.events[-10:]:
            if event.year >= world.year - 3:
                recent_events.append(f"- {event.year}: {event.title_fr}")

        # Major tensions
        tensions = []
        if world.global_tension > 70:
            tensions.append("La tension mondiale est critique")
        if world.defcon_level <= 2:
            tensions.append(f"DEFCON {world.defcon_level} - Risque nucleaire imminent")

        # Player's situation
        player_wars = []
        for enemy_id in player.at_war:
            enemy = world.get_country(enemy_id)
            if enemy:
                player_wars.append(enemy.name_fr)

        player_allies = []
        for ally_id in player.allies[:5]:
            ally = world.get_country(ally_id)
            if ally:
                player_allies.append(ally.name_fr)

        player_rivals = []
        for rival_id in player.rivals[:5]:
            rival = world.get_country(rival_id)
            if rival:
                player_rivals.append(f"{rival.name_fr} (Eco:{rival.economy}, Mil:{rival.military})")

        # Allied countries at war (potential dilemma)
        allies_at_war = []
        for ally_id in player.allies:
            ally = world.get_country(ally_id)
            if ally and ally.at_war:
                for enemy_id in ally.at_war:
                    if enemy_id not in player.at_war:
                        enemy = world.get_country(enemy_id)
                        if enemy:
                            allies_at_war.append(f"{ally.name_fr} attaque par {enemy.name_fr}")

        context = f"""ANNEE: {world.year}

ETAT DU MONDE:
- Tension mondiale: {world.global_tension}/100
- DEFCON: {world.defcon_level}/5
- Prix du petrole: {world.oil_price}$/baril

GUERRES EN COURS:
{wars_text if wars_text else "Aucune guerre majeure"}

EVENEMENTS RECENTS:
{chr(10).join(recent_events[-5:]) if recent_events else "Pas d'evenements majeurs recents"}

SITUATION DU JOUEUR ({player.name_fr}):
- Economie: {player.economy}/100
- Militaire: {player.military}/100
- Stabilite: {player.stability}/100
- Soft Power: {player.soft_power}/100
- Technologie: {player.technology}/100
- Nucleaire: {player.nuclear}/100
- Regime: {player.regime}

ALLIES DU JOUEUR: {', '.join(player_allies) if player_allies else 'Aucun'}
RIVAUX DU JOUEUR: {', '.join(player_rivals) if player_rivals else 'Aucun'}
EN GUERRE AVEC: {', '.join(player_wars) if player_wars else 'Personne'}

ALLIES EN DIFFICULTE:
{chr(10).join(allies_at_war) if allies_at_war else 'Aucun allie en danger'}

TENSIONS CRITIQUES:
{chr(10).join(tensions) if tensions else 'Situation relativement calme'}"""

        return context

    def _build_prompt(self, world: Any, player: Any, event_trigger: str = None) -> str:
        """Build the narrative event generation prompt"""
        context = self._build_world_context(world, player)

        trigger_hint = ""
        if event_trigger:
            trigger_hint = f"\nCONTEXTE SPECIFIQUE: {event_trigger}\n"

        prompt = f"""Tu es un narrateur pour un jeu de simulation geopolitique historique.
Tu dois generer UN evenement realiste et immersif qui affecte le joueur ({player.name_fr}).

{context}
{trigger_hint}

REGLES:
1. L'evenement DOIT etre pertinent pour la situation actuelle du monde
2. L'evenement doit proposer un DILEMME interessant au joueur
3. Les effets doivent etre equilibres (pas trop forts)
4. Le ton doit etre serieux et realiste (style journal/rapport)
5. Utilise des noms de personnes fictifs mais realistes

TYPES D'EVENEMENTS POSSIBLES:
- Crise diplomatique (allie demande aide, incident international)
- Opportunite economique (accord commercial, investissement)
- Menace militaire (mouvements de troupes, provocation)
- Scandale politique (revelation, fuite)
- Catastrophe (naturelle, accident)
- Avancee technologique
- Mouvement social

Reponds UNIQUEMENT avec ce JSON (pas d'autre texte):
{{
  "title_fr": "Titre court et accrocheur",
  "description_fr": "Description narrative de 2-3 phrases, style journalistique",
  "event_type": "crisis|opportunity|diplomatic|military|economic|political|social",
  "severity": "minor|normal|major|critical",
  "effects": [
    {{"stat": "economy|military|stability|soft_power|technology", "delta": -10 a +10}}
  ],
  "choices": [
    {{"id": "choice1", "text_fr": "Option 1", "effect": "Description effet"}},
    {{"id": "choice2", "text_fr": "Option 2", "effect": "Description effet"}}
  ]
}}

Genere un evenement:"""

        return prompt

    async def generate_narrative_event(
        self,
        world: Any,
        player: Any,
        event_trigger: str = None,
        force: bool = False
    ) -> Optional[Event]:
        """Generate a narrative event using AI

        Args:
            world: Current world state
            player: Player's country
            event_trigger: Optional trigger context (e.g., "ally_attacked")
            force: Bypass cooldown check

        Returns:
            Generated Event or None if generation failed/skipped
        """
        # Check cooldown
        if not force and not self._should_generate(player.id, world.year):
            logger.debug(f"AI event generation on cooldown for {player.id}")
            return None

        # Random chance (30% per eligible tick)
        if not force and random.random() > 0.30:
            return None

        prompt = self._build_prompt(world, player, event_trigger)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",  # Request JSON format
                        "options": {
                            "temperature": 0.8,  # More creative
                            "num_predict": 500,
                        },
                    },
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    logger.error(f"AI event generation failed: {response.status_code}")
                    return None

                result = response.json()
                raw_response = result.get("response", "")

                # Parse the generated event
                event = self._parse_ai_response(raw_response, world, player)

                if event:
                    self.last_generated_year[player.id] = world.year
                    logger.info(f"AI generated event: {event.title_fr}")
                    return event

                return None

        except httpx.TimeoutException:
            logger.warning("AI event generation timeout")
            return None
        except httpx.ConnectError:
            logger.warning("AI event generation - Ollama not available")
            return None
        except Exception as e:
            logger.error(f"AI event generation error: {e}")
            return None

    def _parse_ai_response(
        self,
        response: str,
        world: Any,
        player: Any
    ) -> Optional[Event]:
        """Parse AI response into an Event"""
        try:
            # Clean response
            response = response.strip()

            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON in AI response: {response[:100]}")
                return None

            json_str = response[start:end]
            data = json.loads(json_str)

            # Validate required fields
            title_fr = data.get("title_fr", "").strip()
            description_fr = data.get("description_fr", "").strip()

            if not title_fr or not description_fr:
                logger.warning("AI event missing title or description")
                return None

            # Parse effects
            effects = []
            for effect_data in data.get("effects", []):
                stat = effect_data.get("stat")
                delta = effect_data.get("delta", 0)
                if stat and isinstance(delta, (int, float)):
                    # Clamp delta to reasonable range
                    delta = max(-15, min(15, int(delta)))
                    effects.append(EventEffect(stat=stat, delta=delta))

            # Create event
            event_type = data.get("event_type", "ai_narrative")
            severity = data.get("severity", "normal")

            # Map severity to type prefix for display
            type_mapping = {
                "critical": "crisis",
                "major": "warning",
                "minor": "info",
                "normal": "diplomatic"
            }
            display_type = type_mapping.get(severity, event_type)

            event = Event(
                id=f"ai_narrative_{world.year}_{player.id}_{random.randint(1000, 9999)}",
                year=world.year,
                type=display_type,
                title=title_fr,  # Use French as main title
                title_fr=title_fr,
                description=description_fr,
                description_fr=description_fr,
                country_id=player.id,
                effects=effects,
            )

            return event

        except json.JSONDecodeError as e:
            logger.warning(f"AI event JSON parse error: {e}")
            return None
        except Exception as e:
            logger.error(f"AI event parse error: {e}")
            return None


# Global instance
ai_event_generator = AIEventGenerator()


async def generate_ai_event_for_player(
    world: Any,
    player_id: str,
    trigger: str = None
) -> Optional[Event]:
    """Convenience function to generate AI event for player

    Args:
        world: World state
        player_id: Player country ID
        trigger: Optional trigger context

    Returns:
        Generated Event or None
    """
    player = world.get_country(player_id)
    if not player:
        return None

    return await ai_event_generator.generate_narrative_event(
        world=world,
        player=player,
        event_trigger=trigger
    )
