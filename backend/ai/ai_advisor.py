"""AI Advisor System for Historia Lite - Proactive strategic advice and narrative content"""
import asyncio
import logging
import json
import random
from typing import Any, Dict, List, Optional
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from config import settings
from ai.personalities import (
    AdvisorPersonality,
    get_personality,
    get_personality_prompt,
    apply_personality_to_prompt,
    get_all_personalities,
)

logger = logging.getLogger(__name__)


class AdvisorCategory(str, Enum):
    """Categories of AI advisor content"""
    STRATEGIC = "strategic"      # Strategic advice
    DIPLOMATIC = "diplomatic"    # Diplomatic dialogue
    BRIEFING = "briefing"        # Annual briefing
    MEDIA = "media"              # Press commentary
    OPPORTUNITY = "opportunity"  # Positive opportunities


class StrategicAdvice(BaseModel):
    """AI-generated strategic advice"""
    priority: str  # high, medium, low
    category: str  # economy, military, diplomacy, technology, stability
    title_fr: str
    advice_fr: str
    reasoning_fr: str
    suggested_action: Optional[str] = None


class DiplomaticDialogue(BaseModel):
    """AI-generated diplomatic dialogue"""
    speaker_country: str
    speaker_name: str  # Generated leader name
    speaker_title: str  # President, Premier, etc.
    tone: str  # friendly, neutral, hostile, cautious
    message_fr: str
    context: str  # alliance_proposal, sanction_response, etc.


class AnnualBriefing(BaseModel):
    """AI-generated annual intelligence briefing"""
    year: int
    executive_summary_fr: str
    threats: List[Dict[str, str]]  # [{country, threat_level, description}]
    opportunities: List[Dict[str, str]]  # [{domain, description}]
    recommendations: List[str]


class MediaComment(BaseModel):
    """AI-generated press/media commentary"""
    source: str  # Le Monde, The Times, etc.
    headline_fr: str
    excerpt_fr: str
    sentiment: str  # positive, negative, neutral


class AIAdvisor:
    """Comprehensive AI advisor for narrative content generation"""

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
    ):
        self.base_url = base_url or settings.ollama_url
        self.model = model or "qwen2.5:7b"
        self.timeout = 30.0

        # Current personality (can be changed per session)
        self.current_personality: str = AdvisorPersonality.REALIST

        # Cooldowns to avoid spam
        self.last_advice_year: Dict[str, int] = {}
        self.last_briefing_year: int = 0
        self.last_media_year: int = 0

    def set_personality(self, personality_id: str) -> bool:
        """Set the advisor personality"""
        if personality_id in [p.value for p in AdvisorPersonality]:
            self.current_personality = personality_id
            logger.info(f"Advisor personality set to: {personality_id}")
            return True
        return False

    def get_current_personality(self) -> Dict[str, Any]:
        """Get current personality info"""
        return get_personality(self.current_personality)

    def get_available_personalities(self) -> Dict[str, Any]:
        """Get all available personalities"""
        return get_all_personalities()

    async def _call_ollama(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Call Ollama API and return response"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.8,
                            "num_predict": max_tokens,
                        },
                    },
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                return None
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}")
            return None

    def _parse_json(self, response: str) -> Optional[Dict]:
        """Parse JSON from response"""
        try:
            response = response.strip()
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                return None
            return json.loads(response[start:end])
        except json.JSONDecodeError:
            return None

    # =========================================================================
    # STRATEGIC ADVICE
    # =========================================================================

    async def get_strategic_advice(
        self, world: Any, player: Any, focus: str = None, personality: str = None
    ) -> Optional[List[StrategicAdvice]]:
        """Generate proactive strategic advice for the player"""

        # Use specified personality or current default
        active_personality = personality or self.current_personality
        personality_info = get_personality(active_personality)

        # Build context
        context = self._build_player_context(world, player)
        focus_hint = f"\nFocus particulier: {focus}" if focus else ""

        base_prompt = f"""Tu es le conseiller strategique du dirigeant de {player.name_fr}.
Analyse la situation et donne 2-3 conseils strategiques prioritaires.

{context}
{focus_hint}

Reponds UNIQUEMENT avec ce JSON:
{{
  "conseils": [
    {{
      "priority": "high|medium|low",
      "category": "economy|military|diplomacy|technology|stability",
      "title_fr": "Titre court du conseil",
      "advice_fr": "Conseil detaille en 1-2 phrases",
      "reasoning_fr": "Justification basee sur la situation actuelle",
      "suggested_action": "Action concrete suggere (optionnel)"
    }}
  ]
}}"""

        # Apply personality to prompt
        prompt = apply_personality_to_prompt(base_prompt, active_personality)

        response = await self._call_ollama(prompt, 600)
        if not response:
            return None

        data = self._parse_json(response)
        if not data or "conseils" not in data:
            return None

        advices = []
        for c in data["conseils"][:3]:
            try:
                advices.append(StrategicAdvice(
                    priority=c.get("priority", "medium"),
                    category=c.get("category", "general"),
                    title_fr=c.get("title_fr", "Conseil"),
                    advice_fr=c.get("advice_fr", ""),
                    reasoning_fr=c.get("reasoning_fr", ""),
                    suggested_action=c.get("suggested_action")
                ))
            except Exception:
                continue

        return advices if advices else None

    # =========================================================================
    # DIPLOMATIC DIALOGUES
    # =========================================================================

    async def generate_diplomatic_response(
        self,
        world: Any,
        player: Any,
        target_country: Any,
        action_type: str,  # alliance_proposal, sanction, trade_offer, etc.
        accepted: bool = None
    ) -> Optional[DiplomaticDialogue]:
        """Generate a narrative diplomatic response from a country"""

        relation = player.get_relation(target_country.id)
        relation_desc = "cordiales" if relation > 30 else "tendues" if relation < -30 else "neutres"

        # Determine tone based on relation and action
        if accepted is True:
            tone_hint = "positif et cooperatif"
        elif accepted is False:
            tone_hint = "poli mais ferme dans le refus"
        else:
            tone_hint = "diplomatique et mesure"

        prompt = f"""Tu es un ecrivain de dialogues diplomatiques pour un jeu de strategie.
Genere une reponse diplomatique realiste.

CONTEXTE:
- Pays qui repond: {target_country.name_fr}
- Regime: {getattr(target_country, 'regime', 'Republique')}
- Action du joueur ({player.name_fr}): {action_type}
- Relations actuelles: {relation_desc} ({relation}/100)
- Reponse: {"Acceptee" if accepted else "Refusee" if accepted is False else "En attente"}
- Ton attendu: {tone_hint}

Genere un nom fictif realiste pour le dirigeant de {target_country.name_fr}.

Reponds UNIQUEMENT avec ce JSON:
{{
  "speaker_name": "Prenom Nom du dirigeant",
  "speaker_title": "Titre (President, Premier Ministre, etc.)",
  "tone": "friendly|neutral|hostile|cautious",
  "message_fr": "Message diplomatique de 2-3 phrases, style formel mais naturel"
}}"""

        response = await self._call_ollama(prompt, 400)
        if not response:
            return None

        data = self._parse_json(response)
        if not data:
            return None

        try:
            return DiplomaticDialogue(
                speaker_country=target_country.id,
                speaker_name=data.get("speaker_name", "Le dirigeant"),
                speaker_title=data.get("speaker_title", "Dirigeant"),
                tone=data.get("tone", "neutral"),
                message_fr=data.get("message_fr", "Nous prenons note de votre proposition."),
                context=action_type
            )
        except Exception:
            return None

    # =========================================================================
    # ANNUAL BRIEFING
    # =========================================================================

    async def generate_annual_briefing(
        self, world: Any, player: Any
    ) -> Optional[AnnualBriefing]:
        """Generate an annual intelligence briefing for the player"""

        # Check cooldown (one per year)
        if world.year <= self.last_briefing_year:
            return None

        context = self._build_world_context(world, player)

        prompt = f"""Tu es le chef des services de renseignement de {player.name_fr}.
Redige un briefing annuel pour le dirigeant.

{context}

Reponds UNIQUEMENT avec ce JSON:
{{
  "executive_summary_fr": "Resume executif de la situation mondiale en 2-3 phrases",
  "threats": [
    {{"country": "Code pays", "threat_level": "high|medium|low", "description_fr": "Description de la menace"}}
  ],
  "opportunities": [
    {{"domain": "economie|diplomatie|technologie|influence", "description_fr": "Description de l'opportunite"}}
  ],
  "recommendations": ["Recommandation 1", "Recommandation 2"]
}}"""

        response = await self._call_ollama(prompt, 700)
        if not response:
            return None

        data = self._parse_json(response)
        if not data:
            return None

        try:
            briefing = AnnualBriefing(
                year=world.year,
                executive_summary_fr=data.get("executive_summary_fr", "Situation stable."),
                threats=[{
                    "country": t.get("country", ""),
                    "threat_level": t.get("threat_level", "medium"),
                    "description_fr": t.get("description_fr", "")
                } for t in data.get("threats", [])[:3]],
                opportunities=[{
                    "domain": o.get("domain", ""),
                    "description_fr": o.get("description_fr", "")
                } for o in data.get("opportunities", [])[:3]],
                recommendations=data.get("recommendations", [])[:3]
            )
            self.last_briefing_year = world.year
            return briefing
        except Exception:
            return None

    # =========================================================================
    # MEDIA COMMENTARY
    # =========================================================================

    async def generate_media_comment(
        self, world: Any, player: Any, event: Any = None
    ) -> Optional[MediaComment]:
        """Generate a press/media commentary about recent events"""

        # Determine what to comment on
        if event:
            subject = f"Evenement recent: {event.title_fr}"
        else:
            # Pick a random aspect to comment on
            aspects = []
            if player.economy > 70:
                aspects.append("la croissance economique")
            if player.military > 70:
                aspects.append("la puissance militaire")
            if player.stability < 40:
                aspects.append("l'instabilite politique")
            if player.at_war:
                aspects.append("le conflit en cours")
            if not aspects:
                aspects.append("la politique etrangere")
            subject = f"Commentaire sur {random.choice(aspects)} de {player.name_fr}"

        # Random international newspaper
        newspapers = [
            ("Le Monde", "France"),
            ("The Times", "Royaume-Uni"),
            ("The New York Times", "Etats-Unis"),
            ("Der Spiegel", "Allemagne"),
            ("El Pais", "Espagne"),
            ("La Repubblica", "Italie"),
            ("The Guardian", "Royaume-Uni"),
            ("Foreign Affairs", "Etats-Unis"),
        ]
        source, origin = random.choice(newspapers)

        prompt = f"""Tu es un journaliste de {source} ({origin}).
Ecris un court commentaire sur {player.name_fr}.

CONTEXTE:
- Annee: {world.year}
- {subject}
- Economie {player.name_fr}: {player.economy}/100
- Stabilite: {player.stability}/100
- Tension mondiale: {world.global_tension}/100

Reponds UNIQUEMENT avec ce JSON:
{{
  "headline_fr": "Titre accrocheur style presse (max 10 mots)",
  "excerpt_fr": "Extrait d'article de 2-3 phrases, style journalistique professionnel",
  "sentiment": "positive|negative|neutral"
}}"""

        response = await self._call_ollama(prompt, 300)
        if not response:
            return None

        data = self._parse_json(response)
        if not data:
            return None

        try:
            return MediaComment(
                source=source,
                headline_fr=data.get("headline_fr", "Actualite internationale"),
                excerpt_fr=data.get("excerpt_fr", ""),
                sentiment=data.get("sentiment", "neutral")
            )
        except Exception:
            return None

    # =========================================================================
    # POSITIVE OPPORTUNITIES
    # =========================================================================

    async def generate_opportunity_event(
        self, world: Any, player: Any
    ) -> Optional[Dict[str, Any]]:
        """Generate a positive opportunity event"""

        # Determine opportunity type based on player strengths
        opportunities = []
        if player.technology > 60:
            opportunities.append("decouverte scientifique")
        if player.soft_power > 60:
            opportunities.append("succes culturel international")
        if player.economy > 60:
            opportunities.append("opportunite d'investissement")
        if player.stability > 70:
            opportunities.append("attraction de talents etrangers")

        if not opportunities:
            opportunities = ["partenariat international"]

        opp_type = random.choice(opportunities)

        prompt = f"""Tu es un narrateur pour un jeu de simulation geopolitique.
Genere un evenement POSITIF pour {player.name_fr}.

Type d'opportunite: {opp_type}
Annee: {world.year}
Forces du pays: Technologie {player.technology}, Economie {player.economy}, Soft Power {player.soft_power}

Reponds UNIQUEMENT avec ce JSON:
{{
  "title_fr": "Titre positif et engageant",
  "description_fr": "Description narrative de l'opportunite (2-3 phrases)",
  "event_type": "opportunity",
  "effects": [
    {{"stat": "technology|economy|soft_power|stability", "delta": 3 a 8}}
  ]
}}"""

        response = await self._call_ollama(prompt, 350)
        if not response:
            return None

        data = self._parse_json(response)
        if data:
            # Ensure effects are reasonable
            if "effects" in data:
                for effect in data["effects"]:
                    if "delta" in effect:
                        effect["delta"] = max(3, min(10, int(effect["delta"])))
        return data

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _build_player_context(self, world: Any, player: Any) -> str:
        """Build context string for player situation"""
        allies = []
        for ally_id in player.allies[:5]:
            ally = world.get_country(ally_id)
            if ally:
                allies.append(ally.name_fr)

        rivals = []
        for rival_id in player.rivals[:5]:
            rival = world.get_country(rival_id)
            if rival:
                rivals.append(f"{rival.name_fr} (Eco:{rival.economy}, Mil:{rival.military})")

        wars = []
        for enemy_id in player.at_war:
            enemy = world.get_country(enemy_id)
            if enemy:
                wars.append(enemy.name_fr)

        return f"""ANNEE: {world.year}

VOTRE PAYS ({player.name_fr}):
- Economie: {player.economy}/100
- Militaire: {player.military}/100
- Stabilite: {player.stability}/100
- Technologie: {player.technology}/100
- Soft Power: {player.soft_power}/100
- Nucleaire: {player.nuclear}/100

ALLIES: {', '.join(allies) if allies else 'Aucun'}
RIVAUX: {', '.join(rivals) if rivals else 'Aucun'}
EN GUERRE: {', '.join(wars) if wars else 'Non'}

CONTEXTE MONDIAL:
- Tension mondiale: {world.global_tension}/100
- DEFCON: {world.defcon_level}/5
- Prix petrole: {world.oil_price}$"""

    def _build_world_context(self, world: Any, player: Any) -> str:
        """Build broader world context for briefings"""
        base = self._build_player_context(world, player)

        # Add active conflicts
        conflicts = []
        for c in world.countries.values():
            if c.at_war and c.id != player.id:
                for enemy_id in c.at_war[:2]:
                    enemy = world.get_country(enemy_id)
                    if enemy:
                        conflicts.append(f"{c.name_fr} vs {enemy.name_fr}")

        conflict_text = "\n".join(conflicts[:5]) if conflicts else "Aucun conflit majeur"

        return f"""{base}

CONFLITS MONDIAUX:
{conflict_text}"""


    # =========================================================================
    # CONVERSATIONAL CHAT
    # =========================================================================

    async def chat(
        self,
        world: Any,
        player: Any,
        message: str,
        context: dict = None,
        conversation_history: list = None,
        personality: str = None
    ) -> Optional[str]:
        """Have a free-form conversation with the AI advisor"""

        # Use specified personality or current default
        active_personality = personality or self.current_personality
        personality_info = get_personality(active_personality)

        # Build game context
        game_context = self._build_player_context(world, player)

        # Add extra context if provided
        extra_context = ""
        if context:
            if context.get("dilemmas"):
                dilemmas_text = "\n".join([
                    f"- {d.get('title', 'Dilemme')}: {d.get('description', '')}"
                    for d in context["dilemmas"][:3]
                ])
                extra_context += f"\nDILEMMES EN COURS:\n{dilemmas_text}"

            if context.get("recentEvents"):
                events_text = "\n".join([
                    f"- {e.get('year', '')}: {e.get('description', e.get('type', ''))}"
                    for e in context["recentEvents"][:5]
                ])
                extra_context += f"\nEVENEMENTS RECENTS:\n{events_text}"

        # Build conversation history
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:  # Last 4 messages
                role = "Joueur" if msg.get("role") == "user" else "Conseiller"
                history_text += f"{role}: {msg.get('content', '')}\n"

        base_prompt = f"""Tu es un conseiller strategique expert en geopolitique pour le jeu PAX Mundi.
Tu conseilles le dirigeant de {player.name_fr}.

{game_context}
{extra_context}

{f"HISTORIQUE RECENT:{chr(10)}{history_text}" if history_text else ""}

QUESTION DU JOUEUR: {message}

Reponds de maniere concise, strategique et utile en francais.
Donne des conseils actionables bases sur la situation actuelle.
Maximum 3-4 phrases."""

        # Apply personality to prompt
        prompt = apply_personality_to_prompt(base_prompt, active_personality)

        response = await self._call_ollama(prompt, 400)
        if not response:
            return None

        # For chat, we expect plain text, not JSON
        # Try to extract if response contains JSON, otherwise return raw
        try:
            data = self._parse_json(response)
            if data:
                # Check various possible keys the AI might use
                for key in ["response", "message", "conseil", "advice", "answer", "reponse"]:
                    if key in data:
                        return data[key]
                # If it's a dict with a single key, return its value
                if len(data) == 1:
                    return list(data.values())[0]
        except Exception:
            pass

        # Return raw response, cleaned up
        return response.strip().strip('"').strip()


# Global instance
ai_advisor = AIAdvisor()
