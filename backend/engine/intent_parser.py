"""Intent Parser for Historia Narrative

Parses player's natural language input into structured intentions.
Uses LLM (Ollama) to understand free text and extract 30 defined intentions.

Based on Plan: Historia Narrative - 30 Intentions Vocabulary
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# INTENTION TYPES (30 total)
# =============================================================================

class IntentionCategory(str, Enum):
    """Categories of intentions"""
    DIPLOMACY = "diplomacy"
    MILITARY = "military"
    COVERT = "covert"
    INTEL = "intel"
    ECONOMIC = "economic"
    DOMESTIC = "domestic"


class IntentionType(str, Enum):
    """30 intention types from the vocabulary"""
    # Diplomacy (7)
    DIPLO_ALLIANCE = "DIPLO_ALLIANCE"
    DIPLO_THREAT = "DIPLO_THREAT"
    DIPLO_NEGOTIATE = "DIPLO_NEGOTIATE"
    DIPLO_CONCEDE = "DIPLO_CONCEDE"
    DIPLO_SANCTION = "DIPLO_SANCTION"
    DIPLO_SUMMIT = "DIPLO_SUMMIT"
    DIPLO_BACKCHANNEL = "DIPLO_BACKCHANNEL"

    # Military (6)
    MIL_REINFORCE = "MIL_REINFORCE"
    MIL_WITHDRAW = "MIL_WITHDRAW"
    MIL_DEMO = "MIL_DEMO"
    MIL_PROXY = "MIL_PROXY"
    MIL_BLOCKADE = "MIL_BLOCKADE"
    MIL_BASE = "MIL_BASE"

    # Covert (5)
    COV_DESTAB = "COV_DESTAB"
    COV_COUP = "COV_COUP"
    COV_SABOTAGE = "COV_SABOTAGE"
    COV_ASSASSIN = "COV_ASSASSIN"
    COV_PROPAGANDA = "COV_PROPAGANDA"

    # Intel (4)
    INTEL_COLLECT = "INTEL_COLLECT"
    INTEL_VERIFY = "INTEL_VERIFY"
    INTEL_COUNTER = "INTEL_COUNTER"
    INTEL_DISINFO = "INTEL_DISINFO"

    # Economic (4)
    ECO_AID = "ECO_AID"
    ECO_TRADE = "ECO_TRADE"
    ECO_EMBARGO = "ECO_EMBARGO"
    ECO_INVEST = "ECO_INVEST"

    # Domestic (4)
    DOM_SPEECH = "DOM_SPEECH"
    DOM_REFORM = "DOM_REFORM"
    DOM_REPRESS = "DOM_REPRESS"
    DOM_ELECTION = "DOM_ELECTION"


# Intention metadata
INTENTION_METADATA = {
    # Diplomacy
    IntentionType.DIPLO_ALLIANCE: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Proposer alliance",
        "description_fr": "Proposer ou renforcer une alliance avec un pays",
        "keywords": ["alliance", "allier", "renforcer liens", "partenariat", "pacte"],
        "requires_target": True,
        "political_cost": 10,
        "risk_base": "low",
    },
    IntentionType.DIPLO_THREAT: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Menacer",
        "description_fr": "Avertir un pays de consequences negatives",
        "keywords": ["menacer", "avertir", "prevenir", "consequences", "ultimatum"],
        "requires_target": True,
        "political_cost": 15,
        "risk_base": "medium",
    },
    IntentionType.DIPLO_NEGOTIATE: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Negocier",
        "description_fr": "Proposer des negociations sur un sujet",
        "keywords": ["negocier", "discuter", "proposer", "accord", "traite", "pourparlers"],
        "requires_target": True,
        "political_cost": 5,
        "risk_base": "low",
    },
    IntentionType.DIPLO_CONCEDE: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Ceder",
        "description_fr": "Accepter une demande ou faire une concession",
        "keywords": ["ceder", "accepter", "concession", "abandonner", "retirer"],
        "requires_target": False,
        "political_cost": 20,
        "risk_base": "low",
    },
    IntentionType.DIPLO_SANCTION: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Sanctionner",
        "description_fr": "Imposer des sanctions diplomatiques",
        "keywords": ["sanction", "sanctionner", "punir", "represailles", "isoler"],
        "requires_target": True,
        "political_cost": 15,
        "risk_base": "medium",
    },
    IntentionType.DIPLO_SUMMIT: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Organiser sommet",
        "description_fr": "Organiser une rencontre au sommet",
        "keywords": ["sommet", "rencontre", "conference", "reunion", "entretien"],
        "requires_target": True,
        "political_cost": 10,
        "risk_base": "low",
    },
    IntentionType.DIPLO_BACKCHANNEL: {
        "category": IntentionCategory.DIPLOMACY,
        "name_fr": "Canal secret",
        "description_fr": "Etablir un canal de communication discret",
        "keywords": ["secret", "discret", "backchannel", "officieux", "prive"],
        "requires_target": True,
        "political_cost": 5,
        "risk_base": "medium",
    },

    # Military
    IntentionType.MIL_REINFORCE: {
        "category": IntentionCategory.MILITARY,
        "name_fr": "Renforcer",
        "description_fr": "Deployer ou renforcer des forces militaires",
        "keywords": ["renforcer", "deployer", "envoyer troupes", "mobiliser", "positionner"],
        "requires_zone": True,
        "political_cost": 20,
        "risk_base": "medium",
    },
    IntentionType.MIL_WITHDRAW: {
        "category": IntentionCategory.MILITARY,
        "name_fr": "Retirer",
        "description_fr": "Retirer des forces militaires",
        "keywords": ["retirer", "evacuer", "reduire", "rappeler", "demobiliser"],
        "requires_zone": True,
        "political_cost": 10,
        "risk_base": "low",
    },
    IntentionType.MIL_DEMO: {
        "category": IntentionCategory.MILITARY,
        "name_fr": "Demonstration de force",
        "description_fr": "Effectuer une demonstration militaire",
        "keywords": ["demonstration", "montrer force", "exercice", "manoeuvre", "parade"],
        "requires_zone": True,
        "political_cost": 15,
        "risk_base": "medium",
    },
    IntentionType.MIL_PROXY: {
        "category": IntentionCategory.MILITARY,
        "name_fr": "Guerre par procuration",
        "description_fr": "Soutenir des forces alliees locales",
        "keywords": ["proxy", "soutenir forces", "armer", "financer rebelles", "guerre indirecte"],
        "requires_zone": True,
        "political_cost": 25,
        "risk_base": "high",
    },
    IntentionType.MIL_BLOCKADE: {
        "category": IntentionCategory.MILITARY,
        "name_fr": "Blocus",
        "description_fr": "Etablir un blocus naval ou aerien",
        "keywords": ["blocus", "bloquer", "quarantaine", "interdire", "fermer acces"],
        "requires_target": True,
        "political_cost": 30,
        "risk_base": "high",
    },
    IntentionType.MIL_BASE: {
        "category": IntentionCategory.MILITARY,
        "name_fr": "Base militaire",
        "description_fr": "Construire ou etablir une base militaire",
        "keywords": ["base", "installation", "garnison", "avant-poste", "batir"],
        "requires_zone": True,
        "political_cost": 25,
        "risk_base": "medium",
    },

    # Covert
    IntentionType.COV_DESTAB: {
        "category": IntentionCategory.COVERT,
        "name_fr": "Destabiliser",
        "description_fr": "Soutenir l'opposition pour destabiliser",
        "keywords": ["destabiliser", "opposition", "soutenir dissidents", "agiter", "financer opposants"],
        "requires_zone": True,
        "political_cost": 20,
        "risk_base": "high",
    },
    IntentionType.COV_COUP: {
        "category": IntentionCategory.COVERT,
        "name_fr": "Coup d'etat",
        "description_fr": "Organiser un changement de regime",
        "keywords": ["coup", "renverser", "putsch", "regime change", "destituer"],
        "requires_target": True,
        "political_cost": 35,
        "risk_base": "extreme",
    },
    IntentionType.COV_SABOTAGE: {
        "category": IntentionCategory.COVERT,
        "name_fr": "Sabotage",
        "description_fr": "Saboter des installations ennemies",
        "keywords": ["sabotage", "saboter", "detruire", "neutraliser", "endommager"],
        "requires_target": True,
        "political_cost": 25,
        "risk_base": "high",
    },
    IntentionType.COV_ASSASSIN: {
        "category": IntentionCategory.COVERT,
        "name_fr": "Elimination",
        "description_fr": "Neutraliser un leader ennemi",
        "keywords": ["eliminer", "assassiner", "neutraliser leader", "supprimer", "tuer"],
        "requires_target": True,
        "political_cost": 40,
        "risk_base": "extreme",
    },
    IntentionType.COV_PROPAGANDA: {
        "category": IntentionCategory.COVERT,
        "name_fr": "Propagande",
        "description_fr": "Lancer une campagne de propagande",
        "keywords": ["propagande", "campagne", "desinformation", "radio", "tracts"],
        "requires_zone": True,
        "political_cost": 10,
        "risk_base": "low",
    },

    # Intel
    IntentionType.INTEL_COLLECT: {
        "category": IntentionCategory.INTEL,
        "name_fr": "Collecter intel",
        "description_fr": "Collecter des renseignements",
        "keywords": ["renseignement", "collecter", "espionner", "surveiller", "informations"],
        "requires_target": True,
        "political_cost": 10,
        "risk_base": "medium",
    },
    IntentionType.INTEL_VERIFY: {
        "category": IntentionCategory.INTEL,
        "name_fr": "Verifier",
        "description_fr": "Verifier des rapports de renseignement",
        "keywords": ["verifier", "confirmer", "valider", "authentifier", "corroborer"],
        "requires_target": False,
        "political_cost": 5,
        "risk_base": "low",
    },
    IntentionType.INTEL_COUNTER: {
        "category": IntentionCategory.INTEL,
        "name_fr": "Contre-espionnage",
        "description_fr": "Renforcer le contre-espionnage",
        "keywords": ["contre-espionnage", "proteger", "securiser", "chasser taupes", "debusquer"],
        "requires_zone": False,
        "political_cost": 15,
        "risk_base": "low",
    },
    IntentionType.INTEL_DISINFO: {
        "category": IntentionCategory.INTEL,
        "name_fr": "Desinformation",
        "description_fr": "Diffuser de fausses informations",
        "keywords": ["desinformation", "fausses infos", "leurre", "tromper", "intox"],
        "requires_target": True,
        "political_cost": 15,
        "risk_base": "medium",
    },

    # Economic
    IntentionType.ECO_AID: {
        "category": IntentionCategory.ECONOMIC,
        "name_fr": "Aide economique",
        "description_fr": "Envoyer de l'aide economique",
        "keywords": ["aide", "aider", "assistance", "don", "soutien economique"],
        "requires_target": True,
        "political_cost": 15,
        "risk_base": "low",
    },
    IntentionType.ECO_TRADE: {
        "category": IntentionCategory.ECONOMIC,
        "name_fr": "Accord commercial",
        "description_fr": "Etablir des accords commerciaux",
        "keywords": ["commerce", "commercial", "echanges", "trade", "import", "export"],
        "requires_target": True,
        "political_cost": 10,
        "risk_base": "low",
    },
    IntentionType.ECO_EMBARGO: {
        "category": IntentionCategory.ECONOMIC,
        "name_fr": "Embargo",
        "description_fr": "Imposer un embargo economique",
        "keywords": ["embargo", "couper", "interdire commerce", "boycott", "isoler economique"],
        "requires_target": True,
        "political_cost": 20,
        "risk_base": "medium",
    },
    IntentionType.ECO_INVEST: {
        "category": IntentionCategory.ECONOMIC,
        "name_fr": "Investir",
        "description_fr": "Investir dans le developpement",
        "keywords": ["investir", "developper", "financer", "construire", "infrastructure"],
        "requires_zone": True,
        "political_cost": 20,
        "risk_base": "low",
    },

    # Domestic
    IntentionType.DOM_SPEECH: {
        "category": IntentionCategory.DOMESTIC,
        "name_fr": "Discours public",
        "description_fr": "Faire une annonce publique",
        "keywords": ["discours", "annoncer", "declarer", "proclamer", "adresse"],
        "requires_target": False,
        "political_cost": 5,
        "risk_base": "low",
    },
    IntentionType.DOM_REFORM: {
        "category": IntentionCategory.DOMESTIC,
        "name_fr": "Reforme",
        "description_fr": "Lancer des reformes interieures",
        "keywords": ["reforme", "reformer", "changer", "moderniser", "ameliorer"],
        "requires_target": False,
        "political_cost": 25,
        "risk_base": "medium",
    },
    IntentionType.DOM_REPRESS: {
        "category": IntentionCategory.DOMESTIC,
        "name_fr": "Repression",
        "description_fr": "Reprimer l'opposition interieure",
        "keywords": ["reprimer", "repression", "faire taire", "censurer", "arreter"],
        "requires_target": False,
        "political_cost": 15,
        "risk_base": "medium",
    },
    IntentionType.DOM_ELECTION: {
        "category": IntentionCategory.DOMESTIC,
        "name_fr": "Elections",
        "description_fr": "Organiser ou influencer des elections",
        "keywords": ["election", "vote", "scrutin", "democratie", "referendum"],
        "requires_zone": True,
        "political_cost": 20,
        "risk_base": "medium",
    },
}


# =============================================================================
# PARSED INTENTION
# =============================================================================

class ParsedIntention(BaseModel):
    """A single parsed intention from player input"""
    id: str
    type: IntentionType
    category: IntentionCategory

    # Original text that triggered this
    source_text: str

    # Target (zone or country)
    target_zone: Optional[str] = None
    target_country: Optional[str] = None
    topic: Optional[str] = None

    # Extracted parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Confidence of parsing
    confidence: float = 0.8

    # French description
    description_fr: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "category": self.category.value,
            "source_text": self.source_text,
            "target_zone": self.target_zone,
            "target_country": self.target_country,
            "topic": self.topic,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "description_fr": self.description_fr,
        }


class ParseResult(BaseModel):
    """Result of parsing player input"""
    original_text: str
    intentions: List[ParsedIntention] = Field(default_factory=list)
    unrecognized: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "intentions": [i.to_dict() for i in self.intentions],
            "unrecognized": self.unrecognized,
            "warnings": self.warnings,
            "count": len(self.intentions),
        }


# =============================================================================
# ZONE AND COUNTRY MAPPINGS
# =============================================================================

ZONE_ALIASES = {
    # Europe West
    "europe ouest": "europe_west",
    "europe occidentale": "europe_west",
    "otan": "europe_west",
    "nato": "europe_west",
    "france": "europe_west",
    "allemagne": "europe_west",
    "italie": "europe_west",
    "royaume-uni": "europe_west",

    # Europe East
    "europe est": "europe_east",
    "europe orientale": "europe_east",
    "pacte varsovie": "europe_east",
    "bloc sovietique": "europe_east",
    "pologne": "europe_east",
    "tchecoslovaquie": "europe_east",
    "hongrie": "europe_east",
    "berlin": "europe_east",
    "berlin est": "europe_east",

    # Central America
    "amerique centrale": "central_america",
    "cuba": "central_america",
    "mexique": "central_america",
    "caraibes": "central_america",

    # South America
    "amerique sud": "south_america",
    "amerique latine": "south_america",
    "bresil": "south_america",
    "argentine": "south_america",
    "chili": "south_america",

    # Middle East
    "moyen orient": "middle_east",
    "moyen-orient": "middle_east",
    "iran": "middle_east",
    "irak": "middle_east",
    "egypte": "middle_east",
    "israel": "middle_east",
    "syrie": "middle_east",
    "arabie": "middle_east",

    # Africa
    "afrique nord": "north_africa",
    "maghreb": "north_africa",
    "algerie": "north_africa",
    "libye": "north_africa",
    "maroc": "north_africa",

    "afrique": "sub_sahara",
    "afrique sub": "sub_sahara",
    "congo": "sub_sahara",
    "angola": "sub_sahara",

    # Asia
    "asie sud-est": "southeast_asia",
    "vietnam": "southeast_asia",
    "indochine": "southeast_asia",
    "laos": "southeast_asia",
    "cambodge": "southeast_asia",
    "indonesie": "southeast_asia",

    "inde": "south_asia",
    "pakistan": "south_asia",
    "asie sud": "south_asia",

    "extreme orient": "far_east",
    "chine": "far_east",
    "japon": "far_east",
    "coree": "far_east",

    # Other
    "turquie": "turkey_greece",
    "grece": "turkey_greece",
    "scandinavie": "scandinavia",
    "norvege": "scandinavia",
    "suede": "scandinavia",
}

COUNTRY_ALIASES = {
    "urss": "USSR",
    "union sovietique": "USSR",
    "russie": "USSR",
    "moscou": "USSR",
    "sovietiques": "USSR",
    "kremlin": "USSR",
    "khrouchtchev": "USSR",

    "usa": "USA",
    "etats-unis": "USA",
    "amerique": "USA",
    "washington": "USA",
    "kennedy": "USA",
    "americains": "USA",

    "chine": "CHN",
    "pekin": "CHN",
    "mao": "CHN",

    "royaume-uni": "GBR",
    "angleterre": "GBR",
    "londres": "GBR",

    "france": "FRA",
    "paris": "FRA",
    "de gaulle": "FRA",
}


# =============================================================================
# INTENT PARSER
# =============================================================================

class IntentParser:
    """Parses natural language into structured intentions"""

    def __init__(self, ollama_client=None):
        self.ollama = ollama_client
        self._intention_id_counter = 0

    def _next_id(self) -> str:
        """Generate unique intention ID"""
        self._intention_id_counter += 1
        return f"intent_{self._intention_id_counter}"

    async def parse(self, text: str, use_ollama: bool = True) -> ParseResult:
        """Parse player input text into intentions"""
        result = ParseResult(original_text=text)

        # Normalize text
        text_lower = text.lower().strip()

        if use_ollama and self.ollama:
            # Use LLM for parsing
            try:
                llm_result = await self._parse_with_ollama(text)
                if llm_result:
                    result.intentions = llm_result
                    return result
            except Exception as e:
                logger.warning(f"Ollama parsing failed, falling back: {e}")

        # Fallback: keyword-based parsing
        result.intentions = self._parse_keywords(text_lower)

        if not result.intentions:
            result.unrecognized.append(text)
            result.warnings.append("Aucune intention reconnue dans le texte")

        return result

    async def _parse_with_ollama(self, text: str) -> List[ParsedIntention]:
        """Use Ollama LLM to parse text"""
        system_prompt = """Tu es un parseur d'intentions pour un jeu de strategie Guerre Froide.

Le joueur ecrit ce qu'il veut faire comme chef d'etat. Tu dois extraire les INTENTIONS.

INTENTIONS POSSIBLES (30):

DIPLOMATIE:
- DIPLO_ALLIANCE: Proposer alliance (ex: "renforcer nos liens avec...")
- DIPLO_THREAT: Menacer (ex: "avertir que nous n'accepterons pas...")
- DIPLO_NEGOTIATE: Negocier (ex: "proposer un accord sur...")
- DIPLO_CONCEDE: Ceder (ex: "accepter les demandes concernant...")
- DIPLO_SANCTION: Sanctionner (ex: "imposer des sanctions contre...")
- DIPLO_SUMMIT: Sommet (ex: "organiser une rencontre avec...")
- DIPLO_BACKCHANNEL: Canal secret (ex: "contacter discretement...")

MILITAIRE:
- MIL_REINFORCE: Renforcer (ex: "deployer des forces en...")
- MIL_WITHDRAW: Retirer (ex: "reduire notre presence en...")
- MIL_DEMO: Demonstration (ex: "montrer notre force pres de...")
- MIL_PROXY: Proxy war (ex: "soutenir les forces de...")
- MIL_BLOCKADE: Blocus (ex: "etablir un blocus autour de...")
- MIL_BASE: Base (ex: "construire une base en...")

COVERT:
- COV_DESTAB: Destabiliser (ex: "soutenir l'opposition en...")
- COV_COUP: Coup d'etat (ex: "renverser le gouvernement de...")
- COV_SABOTAGE: Sabotage (ex: "saboter les installations de...")
- COV_ASSASSIN: Elimination (ex: "neutraliser le leader de...")
- COV_PROPAGANDA: Propagande (ex: "lancer une campagne contre...")

INTEL:
- INTEL_COLLECT: Collecter (ex: "obtenir des informations sur...")
- INTEL_VERIFY: Verifier (ex: "confirmer les rapports sur...")
- INTEL_COUNTER: Contre-espionnage (ex: "proteger nos operations en...")
- INTEL_DISINFO: Desinformation (ex: "faire croire que...")

ECONOMIE:
- ECO_AID: Aide (ex: "envoyer de l'aide a...")
- ECO_TRADE: Commerce (ex: "etablir des accords avec...")
- ECO_EMBARGO: Embargo (ex: "couper les echanges avec...")
- ECO_INVEST: Investir (ex: "developper l'industrie en...")

DOMESTIQUE:
- DOM_SPEECH: Discours (ex: "annoncer publiquement que...")
- DOM_REFORM: Reforme (ex: "lancer des reformes pour...")
- DOM_REPRESS: Repression (ex: "faire taire l'opposition sur...")
- DOM_ELECTION: Election (ex: "organiser des elections en...")

ZONES:
- europe_west, europe_east, central_america, south_america
- middle_east, north_africa, sub_sahara
- southeast_asia, south_asia, far_east
- turkey_greece, scandinavia

PAYS:
- USSR (URSS, Moscou, Khrouchtchev)
- USA (Etats-Unis, Washington)
- CHN (Chine), GBR (Royaume-Uni), FRA (France)

Reponds en JSON:
{
  "intentions": [
    {
      "type": "INTENTION_TYPE",
      "zone": "zone_id ou null",
      "country": "COUNTRY_CODE ou null",
      "topic": "sujet si pertinent",
      "source": "partie du texte"
    }
  ]
}
"""

        user_prompt = f"Texte du joueur: \"{text}\"\n\nExtrait les intentions:"

        response = await self.ollama.generate(
            model="llama3:8b",
            prompt=user_prompt,
            system=system_prompt,
            format="json"
        )

        # Parse response
        try:
            data = json.loads(response)
            intentions = []

            for item in data.get("intentions", []):
                intent_type = item.get("type", "").upper()

                # Find matching IntentionType
                for it in IntentionType:
                    if it.value == intent_type:
                        meta = INTENTION_METADATA.get(it, {})

                        intention = ParsedIntention(
                            id=self._next_id(),
                            type=it,
                            category=meta.get("category", IntentionCategory.DIPLOMACY),
                            source_text=item.get("source", text),
                            target_zone=item.get("zone"),
                            target_country=item.get("country"),
                            topic=item.get("topic"),
                            confidence=0.85,
                            description_fr=self._build_description(it, item),
                        )
                        intentions.append(intention)
                        break

            return intentions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama JSON: {e}")
            return []

    def _parse_keywords(self, text: str) -> List[ParsedIntention]:
        """Fallback keyword-based parsing"""
        intentions = []

        # Extract zone
        zone = self._extract_zone(text)

        # Extract country
        country = self._extract_country(text)

        # Match against intention keywords
        for intent_type, meta in INTENTION_METADATA.items():
            keywords = meta.get("keywords", [])

            for keyword in keywords:
                if keyword in text:
                    intention = ParsedIntention(
                        id=self._next_id(),
                        type=intent_type,
                        category=meta["category"],
                        source_text=text,
                        target_zone=zone if meta.get("requires_zone") else None,
                        target_country=country if meta.get("requires_target") else None,
                        confidence=0.6,
                        description_fr=self._build_description(intent_type, {
                            "zone": zone,
                            "country": country
                        }),
                    )
                    intentions.append(intention)
                    break  # One intention per type match

        return intentions

    def _extract_zone(self, text: str) -> Optional[str]:
        """Extract zone from text"""
        for alias, zone_id in ZONE_ALIASES.items():
            if alias in text:
                return zone_id
        return None

    def _extract_country(self, text: str) -> Optional[str]:
        """Extract country from text"""
        for alias, country_id in COUNTRY_ALIASES.items():
            if alias in text:
                return country_id
        return None

    def _build_description(self, intent_type: IntentionType, params: Dict) -> str:
        """Build French description for intention"""
        meta = INTENTION_METADATA.get(intent_type, {})
        base = meta.get("name_fr", intent_type.value)

        zone = params.get("zone")
        country = params.get("country")
        topic = params.get("topic")

        zone_names = {
            "europe_west": "Europe de l'Ouest",
            "europe_east": "Europe de l'Est",
            "central_america": "Amerique Centrale",
            "south_america": "Amerique du Sud",
            "middle_east": "Moyen-Orient",
            "north_africa": "Afrique du Nord",
            "sub_sahara": "Afrique Sub-saharienne",
            "southeast_asia": "Asie du Sud-Est",
            "south_asia": "Asie du Sud",
            "far_east": "Extreme-Orient",
            "turkey_greece": "Turquie/Grece",
            "scandinavia": "Scandinavie",
        }

        country_names = {
            "USSR": "l'URSS",
            "USA": "les Etats-Unis",
            "CHN": "la Chine",
            "GBR": "le Royaume-Uni",
            "FRA": "la France",
        }

        if zone:
            zone_name = zone_names.get(zone, zone)
            return f"{base} en {zone_name}"
        elif country:
            country_name = country_names.get(country, country)
            return f"{base} avec {country_name}"
        elif topic:
            return f"{base} concernant {topic}"

        return base


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_intention_cost(intent_type: IntentionType) -> int:
    """Get political cost for an intention"""
    meta = INTENTION_METADATA.get(intent_type, {})
    return meta.get("political_cost", 10)


def get_intention_risk(intent_type: IntentionType) -> str:
    """Get base risk level for an intention"""
    meta = INTENTION_METADATA.get(intent_type, {})
    return meta.get("risk_base", "medium")


def validate_intention(intention: ParsedIntention, state) -> List[str]:
    """Validate intention against current state, return warnings"""
    warnings = []
    meta = INTENTION_METADATA.get(intention.type, {})

    # Check required zone
    if meta.get("requires_zone") and not intention.target_zone:
        warnings.append("Cette action necessite une zone cible")

    # Check required target
    if meta.get("requires_target") and not intention.target_country:
        warnings.append("Cette action necessite un pays cible")

    # Check political capital
    cost = meta.get("political_cost", 10)
    if state.player.political_capital < cost:
        warnings.append(f"Capital politique insuffisant (besoin: {cost})")

    return warnings
