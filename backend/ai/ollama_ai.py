"""Ollama LLM integration for Historia Lite AI decisions

Timeline Backbone Integration:
- AI reads 3-month window for tactical decisions
- AI reads 6-month window for doctrinal changes
- AI reads 12-month window for strategic alliances
- Critical events (importance=5) always visible as "ruptures"
"""
import asyncio
import logging
import httpx
import json
import time
from typing import Optional, Dict, Any, List, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import OrderedDict

from config import settings
from engine.country import Country
from engine.world import World
from engine.events import Event

if TYPE_CHECKING:
    from engine.timeline import TimelineManager

logger = logging.getLogger(__name__)


@dataclass
class CachedDecision:
    """Cached decision with metadata"""
    decision: Dict[str, Any]
    created_tick: int
    situation_hash: str


class DecisionCache:
    """LRU cache for AI decisions with TTL"""

    def __init__(self, max_size: int = 100, ttl_ticks: int = 5):
        self.cache: OrderedDict[str, CachedDecision] = OrderedDict()
        self.max_size = max_size
        self.ttl_ticks = ttl_ticks
        self.hits = 0
        self.misses = 0

    def _make_key(self, country_id: str, situation_hash: str) -> str:
        return f"{country_id}:{situation_hash}"

    def _hash_situation(self, country: Country, world: World) -> str:
        """Create hash of relevant situation factors"""
        factors = [
            country.economy // 10,  # Round to reduce cache misses
            country.military // 10,
            country.stability // 10,
            len(country.at_war),
            len(country.rivals),
            world.global_tension // 20,
            world.defcon_level,
        ]
        return "_".join(str(f) for f in factors)

    def get(self, country: Country, world: World) -> Optional[Dict[str, Any]]:
        """Get cached decision if valid"""
        situation_hash = self._hash_situation(country, world)
        key = self._make_key(country.id, situation_hash)

        if key in self.cache:
            cached = self.cache[key]
            # Check TTL
            if world.year - cached.created_tick <= self.ttl_ticks:
                self.hits += 1
                # Move to end (LRU)
                self.cache.move_to_end(key)
                logger.debug(f"Cache hit for {country.id}")
                return cached.decision
            else:
                # Expired
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, country: Country, world: World, decision: Dict[str, Any]):
        """Cache a decision"""
        situation_hash = self._hash_situation(country, world)
        key = self._make_key(country.id, situation_hash)

        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        self.cache[key] = CachedDecision(
            decision=decision,
            created_tick=world.year,
            situation_hash=situation_hash
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
        }

    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0


class RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self.last_request: Dict[str, float] = {}

    async def wait(self, key: str = "default"):
        """Wait if needed to respect rate limit"""
        now = time.time()
        last = self.last_request.get(key, 0)
        wait_time = self.min_interval - (now - last)

        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request[key] = time.time()


class OllamaAI:
    """AI decision making using Ollama LLM with caching and rate limiting"""

    def __init__(
        self,
        base_url: str = settings.ollama_url,
        model: str = settings.ollama_model,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = settings.ollama_timeout
        self.cache = DecisionCache(
            max_size=100,
            ttl_ticks=getattr(settings, 'ollama_cache_ttl', 5)
        )
        self.rate_limiter = RateLimiter(
            min_interval=getattr(settings, 'ollama_rate_limit', 1.0)
        )
        self.fallback_count = 0
        self.success_count = 0

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
        self,
        country: Country,
        world: World,
        timeline: Optional["TimelineManager"] = None
    ) -> Optional[Dict[str, Any]]:
        """Ask Ollama to make a decision for a country (with caching and fallback)

        Timeline Integration:
        - If timeline provided, includes multi-window context (3/6/12 months)
        - AI makes decisions informed by recent events
        """

        # Check cache first
        cached = self.cache.get(country, world)
        if cached:
            return cached

        # Rate limit
        await self.rate_limiter.wait(key="ollama")

        # Build context prompt (with timeline if available)
        prompt = self._build_prompt(country, world, timeline)

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
                    self.fallback_count += 1
                    return self._algorithmic_fallback(country, world)

                result = response.json()
                decision = self._parse_response(result.get("response", ""), country, world)

                if decision:
                    self.success_count += 1
                    # Cache successful decision
                    self.cache.set(country, world, decision)
                    return decision
                else:
                    self.fallback_count += 1
                    return self._algorithmic_fallback(country, world)

        except httpx.TimeoutException:
            logger.warning(f"Ollama timeout for {country.id} - using fallback")
            self.fallback_count += 1
            return self._algorithmic_fallback(country, world)
        except httpx.ConnectError as e:
            logger.error(f"Ollama connection refused for {country.id}: {e}")
            self.fallback_count += 1
            return self._algorithmic_fallback(country, world)
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error for {country.id}: {e}")
            self.fallback_count += 1
            return self._algorithmic_fallback(country, world)
        except json.JSONDecodeError as e:
            logger.error(f"Ollama response parse error for {country.id}: {e}")
            self.fallback_count += 1
            return self._algorithmic_fallback(country, world)

    def _algorithmic_fallback(
        self, country: Country, world: World
    ) -> Optional[Dict[str, Any]]:
        """Fallback to algorithmic decision when Ollama fails"""
        logger.info(f"[Fallback] Using algorithmic decision for {country.id}")

        # Simple priority-based decision
        actions = []

        # At war? Focus on military
        if country.at_war:
            actions.append(("MILITAIRE", None, "En guerre - renforcement militaire"))

        # Low stability? Fix it
        if country.stability < 40:
            actions.append(("STABILITE", None, "Stabilite critique"))

        # Low economy? Develop
        if country.economy < 50:
            actions.append(("ECONOMIE", None, "Economie faible"))

        # Have rivals and strong? Consider sanctions
        if country.rivals and country.economy > 60:
            rival = country.rivals[0]
            if rival not in country.sanctions_on:
                actions.append(("SANCTIONS", rival, f"Sanction contre {rival}"))

        # Tech behind? Research
        if country.technology < 60 and country.economy > 50:
            actions.append(("TECHNOLOGIE", None, "Retard technologique"))

        # Nuclear program if tier 1-2 and tech high
        if country.tier <= 2 and country.technology >= 70 and country.nuclear < 50:
            actions.append(("NUCLEAIRE", None, "Developpement nucleaire"))

        # Expand influence if stable
        if country.stability > 70 and country.economy > 60:
            actions.append(("INFLUENCE", None, "Expansion d'influence"))

        # Default: economy
        actions.append(("ECONOMIE", None, "Developpement par defaut"))

        # Pick first valid action
        action, target, reason = actions[0]

        decision = {
            "action": action,
            "target": target,
            "reason": reason,
            "is_fallback": True,
        }

        # Cache fallback decision too
        self.cache.set(country, world, decision)
        return decision

    def get_stats(self) -> Dict[str, Any]:
        """Get AI statistics"""
        total = self.success_count + self.fallback_count
        return {
            "success_count": self.success_count,
            "fallback_count": self.fallback_count,
            "success_rate": self.success_count / total if total > 0 else 0,
            "cache_stats": self.cache.get_stats(),
        }

    def _build_prompt(
        self,
        country: Country,
        world: World,
        timeline: Optional["TimelineManager"] = None
    ) -> str:
        """Build the decision prompt for Ollama with multi-window timeline context

        Timeline Windows (Timeline Backbone design):
        - 3 months: Immediate tactical context
        - 6 months: Doctrinal changes
        - 12 months: Strategic alliances
        - Critical events: Major ruptures (always visible)
        """

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

        # Timeline context (multi-window)
        timeline_context = ""
        if timeline:
            ctx = timeline.get_ai_context_multi_window(world.current_date, country.id)

            # Format tactical events (3 months)
            tactical = ctx.get("windows", {}).get("tactical_3m", [])
            if tactical:
                timeline_context += "\n=== EVENEMENTS RECENTS (3 mois) - Decisions tactiques ===\n"
                for e in tactical[:5]:
                    affects = " [TE CONCERNE]" if e.get("affects_observer") else ""
                    timeline_context += f"- {e['date']}: [{e['actor']}] {e['title']} (imp:{e['importance']}){affects}\n"

            # Format doctrinal events (6 months)
            doctrinal = ctx.get("windows", {}).get("doctrinal_6m", [])
            if doctrinal:
                timeline_context += "\n=== EVENEMENTS MOYENS (6 mois) - Changements doctrinaux ===\n"
                for e in doctrinal[:3]:
                    affects = " [TE CONCERNE]" if e.get("affects_observer") else ""
                    timeline_context += f"- {e['date']}: [{e['actor']}] {e['title']}{affects}\n"

            # Format critical events (ruptures)
            critical = ctx.get("windows", {}).get("critical_all", [])
            if critical:
                timeline_context += "\n=== RUPTURES MAJEURES (evenements critiques) ===\n"
                for e in critical[:3]:
                    timeline_context += f"* {e['date']}: {e['title']} [IMPORTANCE 5]\n"

            # Preparation states
            preps = ctx.get("preparation_states", {})
            if preps:
                mil_prep = preps.get("military_mobilization", 0)
                dip_prep = preps.get("diplomatic_channels", 0)
                if mil_prep > 30 or dip_prep > 30:
                    timeline_context += f"\n=== ETAT DE PREPARATION ===\n"
                    if mil_prep > 30:
                        timeline_context += f"- Mobilisation militaire: {mil_prep}%\n"
                    if dip_prep > 30:
                        timeline_context += f"- Canaux diplomatiques: {dip_prep}%\n"

            # Memory scores (sentiment towards other powers)
            memory = ctx.get("country_memory", {})
            if memory and memory.get("total_weighted_impact", 0) > 5:
                timeline_context += f"\n=== MEMOIRE DES EVENEMENTS ===\n"
                if memory.get("conflicts_suffered", 0) > 2:
                    timeline_context += f"- Conflits subis: impact eleve\n"
                if memory.get("conflicts_initiated", 0) > 2:
                    timeline_context += f"- Conflits inities: posture agressive\n"

        # Build the prompt
        prompt = f"""Tu es le dirigeant de {country.name_fr} en {world.date_display}.

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
- Date: {world.date_display}
- DEFCON: {world.defcon_level}
{timeline_context}

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

INSTRUCTIONS:
- Tiens compte des evenements recents dans ta decision
- Les evenements qui te concernent directement [TE CONCERNE] sont prioritaires
- Si des ruptures majeures ont eu lieu, adapte ta strategie en consequence
- Si ta preparation militaire/diplomatique est elevee, tu peux agir plus rapidement

Reponds UNIQUEMENT avec ce format JSON:
{{"action": "NOM_ACTION", "cible": "CODE_PAYS_SI_APPLICABLE", "raison": "explication courte"}}

Exemple: {{"action": "SANCTIONS", "cible": "USA", "raison": "Represailles suite aux sanctions du mois dernier"}}
Exemple: {{"action": "ECONOMIE", "cible": null, "raison": "Priorite a l'economie apres la crise recente"}}

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
