"""Historia Lite - Advanced Strategic AI using Ollama"""
import logging
import httpx
import json
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

from config import settings
from engine.country import Country
from engine.world import World
from engine.events import Event

logger = logging.getLogger(__name__)


class StrategicGoal(str, Enum):
    """High-level strategic goals"""
    REGIONAL_HEGEMONY = "regional_hegemony"
    GLOBAL_POWER = "global_power"
    ECONOMIC_DOMINANCE = "economic_dominance"
    MILITARY_SUPREMACY = "military_supremacy"
    STABILITY_FIRST = "stability_first"
    ALLIANCE_BUILDING = "alliance_building"
    NUCLEAR_DETERRENCE = "nuclear_deterrence"
    DEFENSIVE = "defensive"


class ThreatLevel(str, Enum):
    """Perceived threat levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class StrategicAI:
    """Advanced AI decision making using Ollama with strategic planning"""

    def __init__(
        self,
        base_url: str = settings.ollama_url,
        model: str = settings.ollama_model,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = settings.ollama_timeout

    async def analyze_situation(
        self, country: Country, world: World
    ) -> Dict[str, Any]:
        """Comprehensive situation analysis for a country"""

        # Calculate threat assessment
        threats = self._assess_threats(country, world)

        # Calculate opportunities
        opportunities = self._identify_opportunities(country, world)

        # Determine strategic goal based on situation
        goal = self._determine_strategic_goal(country, world, threats)

        # Analyze relative power
        power_analysis = self._analyze_power_balance(country, world)

        return {
            "threats": threats,
            "opportunities": opportunities,
            "strategic_goal": goal,
            "power_analysis": power_analysis,
            "recommended_actions": self._get_recommended_actions(
                country, world, threats, opportunities, goal
            ),
        }

    def _assess_threats(
        self, country: Country, world: World
    ) -> Dict[str, Dict[str, Any]]:
        """Assess threats to the country"""
        threats = {}

        # Check for war
        if country.at_war:
            for enemy_id in country.at_war:
                enemy = world.get_country(enemy_id)
                if enemy:
                    power_diff = enemy.get_power_score() - country.get_power_score()
                    threat_level = (
                        ThreatLevel.CRITICAL if power_diff > 30 else
                        ThreatLevel.HIGH if power_diff > 10 else
                        ThreatLevel.MEDIUM if power_diff > -10 else
                        ThreatLevel.LOW
                    )
                    threats[enemy_id] = {
                        "type": "war",
                        "level": threat_level.value,
                        "power_diff": power_diff,
                        "nuclear_capable": enemy.nuclear > 0,
                    }

        # Check rivals
        for rival_id in country.rivals:
            if rival_id not in threats:
                rival = world.get_country(rival_id)
                if rival:
                    rel = country.get_relation(rival_id)
                    power_diff = rival.get_power_score() - country.get_power_score()
                    threat_level = (
                        ThreatLevel.HIGH if rel < -60 and power_diff > 20 else
                        ThreatLevel.MEDIUM if rel < -30 else
                        ThreatLevel.LOW
                    )
                    threats[rival_id] = {
                        "type": "rival",
                        "level": threat_level.value,
                        "power_diff": power_diff,
                        "relation": rel,
                    }

        # Global tension threat
        if world.global_tension > 70:
            threats["global_instability"] = {
                "type": "systemic",
                "level": ThreatLevel.HIGH.value if world.global_tension > 85 else ThreatLevel.MEDIUM.value,
                "tension": world.global_tension,
            }

        return threats

    def _identify_opportunities(
        self, country: Country, world: World
    ) -> List[Dict[str, Any]]:
        """Identify strategic opportunities"""
        opportunities = []

        # Economic expansion if stable
        if country.stability > 60 and country.economy < 80:
            opportunities.append({
                "type": "economic_growth",
                "potential": min(100, country.economy + 20),
                "priority": "high" if country.economy < 50 else "medium",
            })

        # Alliance opportunities with non-rivals
        for power_id in ["USA", "CHN", "RUS", "FRA", "GBR", "DEU", "JPN", "IND"]:
            if power_id == country.id:
                continue
            power = world.get_country(power_id)
            if power and power_id not in country.allies and power_id not in country.rivals:
                rel = country.get_relation(power_id)
                if rel > 0:
                    opportunities.append({
                        "type": "alliance",
                        "target": power_id,
                        "relation": rel,
                        "priority": "high" if rel > 30 else "medium",
                    })

        # Nuclear development if tech sufficient
        if country.technology >= 60 and country.nuclear < 30:
            if country.tier <= 2 or country.id in ["IRN", "PRK", "PAK", "ISR"]:
                opportunities.append({
                    "type": "nuclear_program",
                    "current": country.nuclear,
                    "priority": "medium" if not country.at_war else "low",
                })

        # Influence expansion
        if country.soft_power > 50 and country.tier <= 2:
            opportunities.append({
                "type": "influence_expansion",
                "current_soft_power": country.soft_power,
                "priority": "medium",
            })

        return opportunities

    def _determine_strategic_goal(
        self, country: Country, world: World, threats: Dict
    ) -> StrategicGoal:
        """Determine the best strategic goal based on situation"""

        # If at war with stronger enemy, prioritize defense
        critical_threats = [t for t in threats.values() if t.get("level") == "critical"]
        if critical_threats:
            return StrategicGoal.DEFENSIVE

        # If weak militarily, prioritize buildup
        if country.military < 40 and country.tier <= 2:
            return StrategicGoal.MILITARY_SUPREMACY

        # If economy weak, focus on economy
        if country.economy < 40:
            return StrategicGoal.ECONOMIC_DOMINANCE

        # If few allies, build alliances
        if len(country.allies) < 2 and country.tier <= 2:
            return StrategicGoal.ALLIANCE_BUILDING

        # If unstable, prioritize stability
        if country.stability < 50:
            return StrategicGoal.STABILITY_FIRST

        # If nuclear capable rival exists without own deterrent
        for rival_id in country.rivals:
            rival = world.get_country(rival_id)
            if rival and rival.nuclear > 0 and country.nuclear == 0:
                if country.technology >= 60:
                    return StrategicGoal.NUCLEAR_DETERRENCE

        # Default based on tier
        if country.tier == 1:
            return StrategicGoal.GLOBAL_POWER
        elif country.tier == 2:
            return StrategicGoal.REGIONAL_HEGEMONY
        else:
            return StrategicGoal.STABILITY_FIRST

    def _analyze_power_balance(
        self, country: Country, world: World
    ) -> Dict[str, Any]:
        """Analyze power balance in the region and globally"""
        superpowers = world.get_superpowers()

        # Find regional competitors
        regional_powers = []
        for c in world.countries.values():
            if c.id != country.id and c.tier <= country.tier + 1:
                regional_powers.append({
                    "id": c.id,
                    "name": c.name_fr,
                    "power_score": c.get_power_score(),
                    "relation": country.get_relation(c.id),
                    "is_ally": c.id in country.allies,
                    "is_rival": c.id in country.rivals,
                })

        regional_powers.sort(key=lambda x: x["power_score"], reverse=True)

        return {
            "country_rank": self._get_power_rank(country, world),
            "total_countries": len(world.countries),
            "regional_competitors": regional_powers[:5],
            "superpower_relations": {
                sp.id: country.get_relation(sp.id)
                for sp in superpowers if sp.id != country.id
            },
            "bloc_strength": self._calculate_bloc_strength(country, world),
        }

    def _get_power_rank(self, country: Country, world: World) -> int:
        """Get country's rank by power score"""
        sorted_countries = sorted(
            world.countries.values(),
            key=lambda c: c.get_power_score(),
            reverse=True
        )
        for i, c in enumerate(sorted_countries):
            if c.id == country.id:
                return i + 1
        return len(sorted_countries)

    def _calculate_bloc_strength(
        self, country: Country, world: World
    ) -> Dict[str, int]:
        """Calculate combined strength of country's blocs"""
        bloc_strength = {}
        for bloc_name in country.blocs:
            total_power = 0
            member_count = 0
            for c in world.countries.values():
                if bloc_name in c.blocs:
                    total_power += c.get_power_score()
                    member_count += 1
            bloc_strength[bloc_name] = {
                "total_power": total_power,
                "members": member_count,
            }
        return bloc_strength

    def _get_recommended_actions(
        self,
        country: Country,
        world: World,
        threats: Dict,
        opportunities: List,
        goal: StrategicGoal,
    ) -> List[Dict[str, Any]]:
        """Get recommended actions based on analysis"""
        actions = []

        # Based on strategic goal
        if goal == StrategicGoal.DEFENSIVE:
            actions.append({
                "action": "MILITAIRE",
                "priority": 1,
                "reason": "Renforcer les defenses face aux menaces",
            })
            if country.stability < 70:
                actions.append({
                    "action": "STABILITE",
                    "priority": 2,
                    "reason": "Maintenir l'unite nationale en temps de crise",
                })

        elif goal == StrategicGoal.MILITARY_SUPREMACY:
            actions.append({
                "action": "MILITAIRE",
                "priority": 1,
                "reason": "Atteindre la suprematie militaire regionale",
            })
            actions.append({
                "action": "TECHNOLOGIE",
                "priority": 2,
                "reason": "Moderniser les forces armees",
            })

        elif goal == StrategicGoal.ECONOMIC_DOMINANCE:
            actions.append({
                "action": "ECONOMIE",
                "priority": 1,
                "reason": "Developper la puissance economique",
            })

        elif goal == StrategicGoal.ALLIANCE_BUILDING:
            best_ally = None
            best_rel = -100
            for opp in opportunities:
                if opp["type"] == "alliance":
                    if opp["relation"] > best_rel:
                        best_rel = opp["relation"]
                        best_ally = opp["target"]
            if best_ally:
                actions.append({
                    "action": "ALLIANCE",
                    "target": best_ally,
                    "priority": 1,
                    "reason": f"Former une alliance strategique avec {best_ally}",
                })

        elif goal == StrategicGoal.NUCLEAR_DETERRENCE:
            if country.technology >= 60:
                actions.append({
                    "action": "NUCLEAIRE",
                    "priority": 1,
                    "reason": "Developper une capacite de dissuasion nucleaire",
                })
            else:
                actions.append({
                    "action": "TECHNOLOGIE",
                    "priority": 1,
                    "reason": "Developper la technologie pour le programme nucleaire",
                })

        elif goal == StrategicGoal.STABILITY_FIRST:
            actions.append({
                "action": "STABILITE",
                "priority": 1,
                "reason": "Consolider la stabilite interne",
            })

        elif goal == StrategicGoal.REGIONAL_HEGEMONY or goal == StrategicGoal.GLOBAL_POWER:
            # Balanced approach
            if country.economy < country.military:
                actions.append({
                    "action": "ECONOMIE",
                    "priority": 1,
                    "reason": "Equilibrer economie et puissance militaire",
                })
            else:
                actions.append({
                    "action": "INFLUENCE",
                    "priority": 1,
                    "reason": "Etendre l'influence mondiale",
                })

        # Add sanctions against enemies if at war
        for enemy_id, threat_data in threats.items():
            if threat_data.get("type") == "war":
                if enemy_id not in country.sanctions_on:
                    actions.append({
                        "action": "SANCTIONS",
                        "target": enemy_id,
                        "priority": 2,
                        "reason": f"Affaiblir l'economie ennemie de {enemy_id}",
                    })

        return actions[:3]  # Top 3 recommendations

    async def make_strategic_decision(
        self, country: Country, world: World
    ) -> Optional[Dict[str, Any]]:
        """Make a strategic decision using comprehensive analysis and LLM"""

        # First, do algorithmic analysis
        analysis = await self.analyze_situation(country, world)

        # Build enhanced prompt with analysis
        prompt = self._build_strategic_prompt(country, world, analysis)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.6,
                            "num_predict": 500,
                        },
                    },
                    timeout=self.timeout,
                )

                if response.status_code != 200:
                    logger.error(f"Ollama error: {response.status_code}")
                    return self._fallback_decision(analysis)

                result = response.json()
                decision = self._parse_strategic_response(
                    result.get("response", ""), country, world, analysis
                )

                if decision:
                    decision["analysis"] = analysis
                    return decision

                return self._fallback_decision(analysis)

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError) as e:
            logger.warning(f"Ollama unavailable for {country.id}: {e}")
            return self._fallback_decision(analysis)

    def _build_strategic_prompt(
        self, country: Country, world: World, analysis: Dict[str, Any]
    ) -> str:
        """Build enhanced strategic prompt with analysis"""

        threats_text = ""
        if analysis["threats"]:
            threats_lines = []
            for threat_id, data in analysis["threats"].items():
                if data["type"] == "war":
                    threats_lines.append(
                        f"- EN GUERRE avec {threat_id} (niveau: {data['level']}, diff puissance: {data['power_diff']:+d})"
                    )
                elif data["type"] == "rival":
                    threats_lines.append(
                        f"- Rival {threat_id} (niveau: {data['level']}, relation: {data['relation']})"
                    )
            threats_text = "\n".join(threats_lines)

        opportunities_text = ""
        if analysis["opportunities"]:
            opp_lines = []
            for opp in analysis["opportunities"][:3]:
                if opp["type"] == "alliance":
                    opp_lines.append(f"- Alliance possible avec {opp['target']} (relation: {opp['relation']})")
                elif opp["type"] == "economic_growth":
                    opp_lines.append(f"- Croissance economique (potentiel: {opp['potential']})")
                elif opp["type"] == "nuclear_program":
                    opp_lines.append(f"- Programme nucleaire (actuel: {opp['current']})")
            opportunities_text = "\n".join(opp_lines)

        recommended = "\n".join([
            f"- {r['action']} ({r.get('target', 'N/A')}): {r['reason']}"
            for r in analysis["recommended_actions"]
        ])

        prompt = f"""Tu es le conseiller strategique de {country.name_fr} en {world.year}.

== ANALYSE STRATEGIQUE ==

OBJECTIF STRATEGIQUE: {analysis['strategic_goal'].value.replace('_', ' ').title()}
RANG MONDIAL: #{analysis['power_analysis']['country_rank']}/{analysis['power_analysis']['total_countries']}

SITUATION ACTUELLE:
- Economie: {country.economy}/100
- Militaire: {country.military}/100
- Nucleaire: {country.nuclear}/100
- Technologie: {country.technology}/100
- Stabilite: {country.stability}/100
- Soft Power: {country.soft_power}/100

MENACES IDENTIFIEES:
{threats_text if threats_text else "Aucune menace majeure"}

OPPORTUNITES:
{opportunities_text if opportunities_text else "Aucune opportunite immediate"}

ACTIONS RECOMMANDEES PAR L'ANALYSE:
{recommended}

CONTEXTE:
- Tension mondiale: {world.global_tension}/100
- Prix petrole: {world.oil_price}$/baril
- Allies: {', '.join(country.allies[:5]) if country.allies else 'Aucun'}
- Blocs: {', '.join(country.blocs) if country.blocs else 'Aucun'}

== DECISION REQUISE ==

En tant que conseiller, choisis UNE action parmi:
ECONOMIE, MILITAIRE, TECHNOLOGIE, STABILITE, INFLUENCE, SANCTIONS, ALLIANCE, NUCLEAIRE, RIEN

Reponds STRICTEMENT en JSON:
{{"action": "ACTION", "cible": "CODE_PAYS_OU_NULL", "raison": "justification strategique", "risques": "risques potentiels"}}

Ta recommendation strategique:"""

        return prompt

    def _parse_strategic_response(
        self,
        response: str,
        country: Country,
        world: World,
        analysis: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Parse strategic response from Ollama"""
        try:
            response = response.strip()
            start = response.find("{")
            end = response.rfind("}") + 1

            if start == -1 or end == 0:
                return None

            json_str = response[start:end]
            decision = json.loads(json_str)

            valid_actions = [
                "ECONOMIE", "MILITAIRE", "TECHNOLOGIE", "STABILITE",
                "INFLUENCE", "SANCTIONS", "ALLIANCE", "NUCLEAIRE", "RIEN"
            ]

            action = decision.get("action", "").upper()
            if action not in valid_actions:
                return None

            return {
                "action": action,
                "target": decision.get("cible"),
                "reason": decision.get("raison", ""),
                "risks": decision.get("risques", ""),
                "raw_response": response,
                "strategic_goal": analysis["strategic_goal"].value,
            }

        except json.JSONDecodeError:
            return None

    def _fallback_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to algorithmic decision if Ollama unavailable"""
        if analysis["recommended_actions"]:
            rec = analysis["recommended_actions"][0]
            return {
                "action": rec["action"],
                "target": rec.get("target"),
                "reason": rec["reason"],
                "risks": "Decision algorithmique (Ollama indisponible)",
                "strategic_goal": analysis["strategic_goal"].value,
                "analysis": analysis,
                "fallback": True,
            }

        return {
            "action": "RIEN",
            "target": None,
            "reason": "Maintien du statu quo",
            "risks": "Stagnation possible",
            "strategic_goal": analysis["strategic_goal"].value,
            "analysis": analysis,
            "fallback": True,
        }


async def get_geopolitical_analysis(world: World) -> Dict[str, Any]:
    """Get comprehensive geopolitical analysis of the world state"""

    # Power distribution
    power_by_tier = {1: [], 2: [], 3: [], 4: []}
    for country in world.countries.values():
        power_by_tier[country.tier].append({
            "id": country.id,
            "name": country.name_fr,
            "power_score": country.get_power_score(),
        })

    for tier in power_by_tier:
        power_by_tier[tier].sort(key=lambda x: x["power_score"], reverse=True)

    # Active conflicts
    conflicts = []
    seen_conflicts = set()
    for country in world.countries.values():
        for enemy_id in country.at_war:
            conflict_key = tuple(sorted([country.id, enemy_id]))
            if conflict_key not in seen_conflicts:
                seen_conflicts.add(conflict_key)
                enemy = world.get_country(enemy_id)
                conflicts.append({
                    "parties": [country.id, enemy_id],
                    "power_balance": country.get_power_score() - (enemy.get_power_score() if enemy else 0),
                })

    # Bloc analysis
    bloc_power = {}
    for country in world.countries.values():
        for bloc in country.blocs:
            if bloc not in bloc_power:
                bloc_power[bloc] = {"members": 0, "total_power": 0, "nuclear": False}
            bloc_power[bloc]["members"] += 1
            bloc_power[bloc]["total_power"] += country.get_power_score()
            if country.nuclear > 0:
                bloc_power[bloc]["nuclear"] = True

    # Hot zones (high tension areas)
    hot_zones = []
    for zone_id, zone in world.influence_zones.items():
        if len(zone.contested_by) >= 2:
            hot_zones.append({
                "zone": zone_id,
                "dominant": zone.dominant_power,
                "contested_by": zone.contested_by,
                "tension_factor": len(zone.contested_by) * 10,
            })

    return {
        "year": world.year,
        "global_tension": world.global_tension,
        "oil_price": world.oil_price,
        "power_distribution": power_by_tier,
        "active_conflicts": conflicts,
        "bloc_analysis": bloc_power,
        "hot_zones": hot_zones[:5],
        "nuclear_powers": [
            c.id for c in world.countries.values() if c.nuclear > 0
        ],
        "defcon_level": world.defcon_level,
    }


# Global strategic AI instance
strategic_ai = StrategicAI()
