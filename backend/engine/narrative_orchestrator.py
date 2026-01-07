"""
Narrative Orchestrator - Le Chef d'Orchestre

Transforme les metriques en histoires.
Le joueur ne voit jamais de chiffres, juste du narratif.

CE MODULE ORCHESTRE TOUS LES SYSTEMES EXISTANTS:
- ai_advisor.py: Dialogues diplomatiques, commentaires media
- media_sources.py: 40+ sources avec biais editoriaux
- timeline.py: Chaines causales, contexte multi-fenetre
- domino_effects.py: Contagion entre zones adjacentes
- personalities.py: Personnalites des conseillers

Le joueur vit une HISTOIRE, pas des metriques.
"""

import logging
import random
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ai.ai_advisor import AIAdvisor
    from engine.timeline import TimelineManager, TimelineEvent

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class LeaderDialogue:
    """Dialogue d'un leader - genere par AI ou templates"""
    speaker: str          # "Nikita Khrouchtchev"
    title: str            # "Premier Secretaire"
    tone: str             # angry, pleased, threatening, neutral, cautious
    message: str          # Le dialogue lui-meme
    country: Optional[str] = None
    portrait_style: str = "cold_war"  # Pour le frontend

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PressHeadline:
    """Depeche de presse - utilise les 40+ sources de media_sources.py"""
    source: str           # "Le Monde", "The New York Times", "Pravda"
    source_id: str        # ID interne (nyt, le_monde, pravda)
    headline: str         # Titre principal
    excerpt: str          # Extrait de l'article
    sentiment: str        # positive, negative, neutral
    bias: str             # pro_west, pro_east, neutral, etc.
    country: str          # Pays d'origine de la source
    credibility: str      # high, medium, tabloid

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class IntelReport:
    """Rapport de renseignement"""
    classification: str   # TOP SECRET, CONFIDENTIAL, SECRET
    content: str          # Contenu du rapport
    reliability: str      # certain, likely, uncertain, rumor
    source_type: str      # humint, sigint, imagery
    analyst_note: Optional[str] = None  # Note d'analyste optionnelle

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CausalContext:
    """Contexte causal - d'ou vient cet evenement, ou mene-t-il?"""
    caused_by: Optional[str] = None      # Titre de l'evenement declencheur
    caused_by_date: Optional[str] = None
    effects_preview: List[str] = field(default_factory=list)  # Consequences probables
    domino_zones: List[str] = field(default_factory=list)     # Zones adjacentes affectees

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class NarrativeScene:
    """Une scene narrative complete a afficher au joueur"""

    # Recit principal (toujours present)
    narrative: str

    # Elements optionnels (le chef decide ce qui est pertinent)
    leader_dialogue: Optional[LeaderDialogue] = None
    press_headlines: List[PressHeadline] = field(default_factory=list)  # Multiple perspectives!
    intel_report: Optional[IntelReport] = None
    causal_context: Optional[CausalContext] = None

    # Teaser pour la suite
    consequence_teaser: Optional[str] = None

    # Metadata pour le frontend
    mood: str = "neutral"         # tense, hopeful, dark, triumphant, neutral
    importance: str = "normal"    # minor, normal, major, critical

    # Contexte
    year: Optional[int] = None
    month: Optional[int] = None
    zone: Optional[str] = None
    zone_name_fr: Optional[str] = None
    event_type: Optional[str] = None

    # Flags pour le frontend
    is_player_caused: bool = False
    is_crisis: bool = False
    is_turning_point: bool = False  # Moment charniere de l'histoire

    def to_dict(self) -> Dict:
        result = {
            "narrative": self.narrative,
            "mood": self.mood,
            "importance": self.importance,
            "year": self.year,
            "month": self.month,
            "zone": self.zone,
            "zone_name_fr": self.zone_name_fr,
            "event_type": self.event_type,
            "consequence_teaser": self.consequence_teaser,
            "is_player_caused": self.is_player_caused,
            "is_crisis": self.is_crisis,
            "is_turning_point": self.is_turning_point,
        }
        if self.leader_dialogue:
            result["leader_dialogue"] = self.leader_dialogue.to_dict()
        if self.press_headlines:
            result["press_headlines"] = [p.to_dict() for p in self.press_headlines]
        if self.intel_report:
            result["intel_report"] = self.intel_report.to_dict()
        if self.causal_context:
            result["causal_context"] = self.causal_context.to_dict()
        return result


# =============================================================================
# ZONE NAMES
# =============================================================================

ZONE_NAMES_FR = {
    "central_america": "Amerique Centrale",
    "south_america": "Amerique du Sud",
    "europe_west": "Europe de l'Ouest",
    "europe_east": "Europe de l'Est",
    "middle_east": "Moyen-Orient",
    "north_africa": "Afrique du Nord",
    "africa_sub": "Afrique Subsaharienne",
    "southeast_asia": "Asie du Sud-Est",
    "south_asia": "Asie du Sud",
    "far_east": "Extreme-Orient",
    "turkey_greece": "Turquie-Grece",
    "scandinavia": "Scandinavie",
}


# =============================================================================
# LEADER DATABASE
# =============================================================================

WORLD_LEADERS = {
    "USA": {"name": "John F. Kennedy", "title": "President des Etats-Unis", "style": "charismatic"},
    "USSR": {"name": "Nikita Khrouchtchev", "title": "Premier Secretaire du PCUS", "style": "confrontational"},
    "FRA": {"name": "Charles de Gaulle", "title": "President de la Republique", "style": "proud"},
    "GBR": {"name": "Harold Macmillan", "title": "Premier Ministre", "style": "diplomatic"},
    "CHN": {"name": "Mao Zedong", "title": "President de la RPC", "style": "revolutionary"},
    "DEU": {"name": "Konrad Adenauer", "title": "Chancelier federal", "style": "cautious"},
    "CUB": {"name": "Fidel Castro", "title": "Premier Ministre", "style": "defiant"},
    "EGY": {"name": "Gamal Abdel Nasser", "title": "President", "style": "nationalist"},
    "IND": {"name": "Jawaharlal Nehru", "title": "Premier Ministre", "style": "non_aligned"},
    "BRA": {"name": "Joao Goulart", "title": "President", "style": "populist"},
}


# =============================================================================
# NARRATIVE TEMPLATES (FALLBACK WHEN AI NOT AVAILABLE)
# =============================================================================

NARRATIVE_TEMPLATES = {
    # Military
    "MIL_REINFORCE": [
        "Des convois militaires traversent {zone_fr}. Les forces {actor} renforcent leurs positions.",
        "Le Pentagone annonce le deploiement de troupes en {zone_fr}. La tension monte dans la region.",
        "Mobilisation en {zone_fr}. Les bases bourdonnent d'activite. L'adversaire observe, inquiet.",
    ],
    "MIL_BLOCKADE": [
        "Les destroyers encerclent {zone_fr}. Blocus total. Le monde retient son souffle.",
        "La marine a deploye sa puissance. {zone_fr} est desormais sous quarantaine navale.",
        "Le blocus est en place. Aucun navire ne passera. La ligne rouge est tracee.",
    ],
    "MIL_DEMO": [
        "Les missiles decollent dans un rugissement. Une demonstration de force qui fait trembler le monde.",
        "Exercices militaires en {zone_fr}. Le tonnerre des canons resonne comme un avertissement.",
        "Les bombardiers survolent la region. Le message est clair, implacable.",
    ],
    "MIL_PROXY": [
        "Des armes affluent vers {zone_fr}. Une guerre par procuration s'installe dans l'ombre.",
        "Les conseillers militaires debarquent discretement. Le conflit s'internationalise.",
        "Livraisons d'armes en {zone_fr}. Les grandes puissances s'affrontent sans se regarder.",
    ],

    # Diplomacy
    "DIPLO_ALLIANCE": [
        "Poignees de main fermes a {zone_fr}. Une alliance se noue dans les salons feutres.",
        "Les drapeaux flottent cote a cote. {zone_fr} rejoint la sphere d'influence.",
        "Accord historique signe. Le monde bipolaire gagne un nouveau pion.",
    ],
    "DIPLO_SUMMIT": [
        "Les limousines s'alignent. Le sommet de {zone_fr} s'ouvre sous les flashs des photographes.",
        "Derriere les portes closes, les dirigeants negocient l'avenir du monde.",
        "Sommet au plus haut niveau. Chaque mot sera analyse par les chancelleries.",
    ],
    "DIPLO_THREAT": [
        "L'avertissement claque comme un coup de fouet. Les consequences seront severes.",
        "Un ultimatum a peine voile. La ligne rouge est tracee en {zone_fr}.",
        "Les mots sont durs, la menace explicite. La diplomatie atteint ses limites.",
    ],
    "DIPLO_SANCTION": [
        "Les sanctions tombent comme un couperet. L'economie de {zone_fr} vacille.",
        "Embargo declare. Les ports se ferment, les usines ralentissent.",
        "Mesures punitives annoncees. L'etau se resserre sur {zone_fr}.",
    ],

    # Covert
    "COV_DESTAB": [
        "Dans l'ombre de {zone_fr}, des hommes sans visage preparent le terrain.",
        "Les agents sont en place. L'operation de destabilisation commence.",
        "Des rumeurs se repandent, des troubles eclatent. Personne ne sait d'ou vient le vent.",
    ],
    "COV_COUP": [
        "Cette nuit, des hommes armes se deploient dans les rues. Le gouvernement ne verra pas l'aube.",
        "Operation en cours. Les communications sont coupees, les chars encerclent le palais.",
        "Coup d'Etat en {zone_fr}. Au petit matin, un nouveau regime emerge des decombres.",
    ],
    "COV_PROPAGANDA": [
        "Les tracts pleuvent sur {zone_fr}. La guerre des idees fait rage.",
        "Radio Liberty emet vers l'Est. Les ondes portent un message de liberte... ou de subversion.",
        "La propagande s'infiltre partout. Les coeurs et les esprits sont le champ de bataille.",
    ],
    "COV_ASSASSIN": [
        "Un homme s'effondre dans les rues de {zone_fr}. L'operation est terminee.",
        "L'agent a frappe. Le regime perd l'un de ses piliers.",
        "Mort suspecte en {zone_fr}. Les services secrets ne commentent pas.",
    ],

    # Economic
    "ECO_AID": [
        "Les cargaisons d'aide arrivent en {zone_fr}. La gratitude... ou la dependance?",
        "Programme d'assistance lance. L'influence s'achete aussi avec des dollars.",
        "Aide economique massive pour {zone_fr}. Un investissement dans l'avenir... politique.",
    ],
    "ECO_EMBARGO": [
        "Les frontieres economiques se ferment. {zone_fr} se retrouve isolee.",
        "Embargo total declare. Les reserves s'epuisent, la population souffre.",
        "Blocus economique. L'arme du portefeuille frappe sans pitie.",
    ],

    # Crisis
    "crisis_erupted": [
        "CRISE EN {zone_fr}! Les nouvelles tombent comme des coups de tonnerre.",
        "Le monde retient son souffle. La situation en {zone_fr} se deteriore rapidement.",
        "Alerte rouge. Les chancelleries s'agitent, les telephones sonnent sans cesse.",
        "Flash special. Les ambassadeurs sont rappeles, les avions decollent.",
        "Situation critique en {zone_fr}. Le Conseil de securite se reunit en urgence.",
    ],
    "crisis_escalated": [
        "La crise s'aggrave en {zone_fr}. Les options se reduisent, les risques augmentent.",
        "Escalade en {zone_fr}. Chaque heure rapproche le monde de l'abime.",
        "Point de non-retour approche en {zone_fr}. Les decisions prises maintenant marqueront l'Histoire.",
        "Les negociations echouent. En {zone_fr}, les armes parlent plus fort que la diplomatie.",
        "Ultimatum expire. La tension atteint des sommets jamais vus depuis 1945.",
    ],
    "crisis_deescalated": [
        "La tension retombe en {zone_fr}. Un soupir de soulagement traverse les capitales.",
        "Recul tactique. Quelqu'un a choisi de ne pas appuyer sur le bouton.",
        "Canal diplomatique retabli. Les mots remplacent a nouveau les menaces.",
        "Le pire a ete evite. Cette fois.",
        "Accord de principe en {zone_fr}. La paix reste fragile, mais elle tient.",
    ],

    # Default - ENRICHI pour eviter la repetition
    "default": [
        "Les evenements se precipitent en {zone_fr}. L'histoire s'ecrit sous nos yeux.",
        "En {zone_fr}, la situation evolue. Les consequences restent a determiner.",
        "Nouvelle donne en {zone_fr}. Les equilibres vacillent.",
        "Mouvement en {zone_fr}. Les chancelleries ajustent leurs calculs.",
        "Le silence radio est rompu. Des nouvelles arrivent de {zone_fr}.",
        "Bulletin special. La situation en {zone_fr} requiert votre attention.",
        "Les pions bougent sur l'echiquier. {zone_fr} entre dans une nouvelle phase.",
        "Rapport de situation: {zone_fr} reste sous haute surveillance.",
    ],

    # Adversary actions - NEW
    "adversary_reinforce": [
        "L'URSS renforce ses positions en {zone_fr}. Moscou avance ses pions.",
        "Mouvement sovietique detecte. Des conseillers arrivent en {zone_fr}.",
        "Les Rouges etendent leur influence en {zone_fr}. Sans bruit, mais inexorablement.",
        "Cargaison suspecte signalee en route vers {zone_fr}. Contenu: materiel militaire.",
    ],
    "adversary_pressure": [
        "Moscou hausse le ton. La pression s'intensifie sur {zone_fr}.",
        "Ultimatum voile de l'URSS. {zone_fr} doit choisir son camp.",
        "Khrouchtchev tape du poing. Le message est clair.",
        "Les services sovietiques s'activent en {zone_fr}. Nous avons des yeux partout.",
    ],

    # Player actions - feedback
    "player_success": [
        "Votre initiative porte ses fruits en {zone_fr}. L'influence americaine grandit.",
        "Operation reussie. {zone_fr} penche un peu plus vers l'Ouest.",
        "La diplomatie americaine marque des points. Moscou fulmine.",
        "Victoire discrete mais decisive en {zone_fr}.",
    ],
    "player_risky": [
        "Votre decision audacieuse fait trembler {zone_fr}. Le monde retient son souffle.",
        "Pari risque en {zone_fr}. L'Histoire jugera.",
        "Les conseillers sont nerveux. Cette manoeuvre en {zone_fr} pourrait mal tourner.",
        "Coup de poker en {zone_fr}. Les des sont jetes.",
    ],
}


# =============================================================================
# INTEL TEMPLATES
# =============================================================================

INTEL_TEMPLATES = {
    "COV_DESTAB": "HUMINT: Nos agents rapportent des mouvements d'opposition en {zone_fr}. L'operation suit son cours. Couverture intacte.",
    "COV_COUP": "FLASH: Operation en cours en {zone_fr}. Contact perdu avec l'equipe principale. Attendons confirmation. Preparer extraction.",
    "COV_PROPAGANDA": "SIGINT: Distribution de materiel en {zone_fr} achevee a 70%. Reception favorable parmi la population cible. Budget respecte.",
    "COV_SABOTAGE": "HUMINT: Cible neutralisee en {zone_fr}. Equipe d'extraction en route. Aucun temoin. Plausible deniability maintenue.",
    "COV_ASSASSIN": "FLASH PRIORITY: Sujet elimine. Operation chirurgicale. Zero trace. Attendons retombees politiques sous 48h.",
    "INTEL_COLLECT": "SIGINT: Nouvelles sources activees en {zone_fr}. Flux d'informations en augmentation. Recoupement en cours.",
    "default": "SITUATION REPORT: {zone_fr} sous surveillance. Prochaine mise a jour dans 48h. Aucune anomalie detectee.",
}


# =============================================================================
# NARRATIVE ORCHESTRATOR
# =============================================================================

class NarrativeOrchestrator:
    """
    Chef d'orchestre qui compose des scenes narratives.

    UTILISE TOUS LES SYSTEMES EXISTANTS:
    - AIAdvisor pour generation dynamique de dialogues et articles
    - MediaSourceManager pour les 40+ sources avec biais
    - Timeline pour le contexte causal
    - Domino effects pour les zones adjacentes

    Le joueur ne voit jamais de chiffres, juste du narratif.
    """

    def __init__(
        self,
        ai_advisor: Optional["AIAdvisor"] = None,
        timeline: Optional["TimelineManager"] = None,
        use_ai: bool = True,
    ):
        """
        Args:
            ai_advisor: Instance de AIAdvisor pour generation AI
            timeline: Instance de TimelineManager pour contexte causal
            use_ai: Si True, utilise l'AI pour generer du contenu dynamique
        """
        self.ai_advisor = ai_advisor
        self.timeline = timeline
        self.use_ai = use_ai and ai_advisor is not None

        # Import des systemes existants
        try:
            from ai.media_sources import (
                get_random_source,
                get_contrasting_sources,
                select_source_for_event,
                get_source_prompt_enhancement,
                MEDIA_SOURCES,
            )
            self._media_sources = MEDIA_SOURCES
            self._get_random_source = get_random_source
            self._get_contrasting_sources = get_contrasting_sources
            self._select_source_for_event = select_source_for_event
            self._has_media_sources = True
        except ImportError:
            self._has_media_sources = False
            logger.warning("media_sources not available, using fallback")

        try:
            from engine.domino_effects import (
                calculate_domino_bonus,
                get_regional_tension,
                get_contagion_risk,
                ADJACENT_ZONES,
            )
            self._calculate_domino_bonus = calculate_domino_bonus
            self._get_regional_tension = get_regional_tension
            self._get_contagion_risk = get_contagion_risk
            self._adjacent_zones = ADJACENT_ZONES
            self._has_domino = True
        except ImportError:
            self._has_domino = False
            logger.warning("domino_effects not available")

    async def compose_scene(
        self,
        event_type: str,
        zone_id: str = None,
        effects: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        caused_by: str = None,
        effects_chain: List[Dict] = None,
        importance: str = "normal",
        player_caused: bool = False,
        actor_country: str = "USA",
        target_countries: List[str] = None,
        timeline_event: "TimelineEvent" = None,
        all_zones: Dict = None,
    ) -> NarrativeScene:
        """
        Compose une scene narrative complete.

        UTILISE TOUS LES SYSTEMES:
        - Genere le recit principal
        - Ajoute dialogues de leaders (AI ou templates)
        - Ajoute perspectives presse multiples (40+ sources)
        - Ajoute rapport intel si covert
        - Ajoute contexte causal (chaines d'evenements)
        - Calcule effets domino

        Args:
            event_type: Type d'evenement (MIL_BLOCKADE, DIPLO_SUMMIT, etc.)
            zone_id: Zone concernee
            effects: Effets de l'evenement (influence, stability, etc.)
            context: Etat du monde (defcon, tension, year)
            caused_by: Evenement qui a cause celui-ci
            effects_chain: Consequences probables
            importance: Niveau d'importance (minor, normal, major, critical)
            player_caused: Si le joueur a declenche cet evenement
            actor_country: Pays acteur (USA, USSR, etc.)
            target_countries: Pays cibles
            timeline_event: Evenement TimelineEvent complet si disponible
            all_zones: Dict de toutes les zones pour effets domino

        Returns:
            NarrativeScene prete a afficher
        """
        effects = effects or {}
        context = context or {}
        target_countries = target_countries or []

        zone_fr = ZONE_NAMES_FR.get(zone_id, zone_id or "la region")
        year = context.get("year", 1962)
        month = context.get("month", 10)
        defcon = context.get("defcon", 4)

        # 1. Generer le recit principal
        narrative = await self._generate_narrative(
            event_type, zone_fr, effects, context, actor_country, player_caused
        )

        # 2. Creer la scene de base
        scene = NarrativeScene(
            narrative=narrative,
            mood=self._determine_mood(event_type, effects, context, defcon),
            importance=importance,
            year=year,
            month=month,
            zone=zone_id,
            zone_name_fr=zone_fr,
            event_type=event_type,
            is_player_caused=player_caused,
            is_crisis="crisis" in event_type.lower() or defcon <= 2,
            is_turning_point=importance == "critical" or defcon <= 2,
        )

        # 3. DIALOGUES DE LEADERS (AI ou templates)
        if self._needs_leader_reaction(event_type, importance, effects, defcon):
            scene.leader_dialogue = await self._get_leader_dialogue(
                event_type, effects, context, player_caused, actor_country, target_countries
            )

        # 4. PERSPECTIVES PRESSE MULTIPLES (40+ sources!)
        if self._is_public_event(event_type, importance):
            scene.press_headlines = await self._get_press_headlines(
                event_type, zone_fr, effects, context, actor_country
            )

        # 5. RAPPORT INTEL (si covert)
        if self._is_covert_event(event_type):
            scene.intel_report = self._get_intel_report(event_type, zone_fr, effects)

        # 6. CONTEXTE CAUSAL (chaines d'evenements)
        scene.causal_context = self._build_causal_context(
            event_type, zone_id, caused_by, effects_chain, timeline_event, all_zones
        )

        # 7. TEASER CONSEQUENCE
        if effects_chain:
            scene.consequence_teaser = self._format_consequence_teaser(effects_chain)
        elif scene.causal_context and scene.causal_context.effects_preview:
            scene.consequence_teaser = f"Ceci pourrait mener a: {scene.causal_context.effects_preview[0]}..."

        logger.debug(
            f"Scene composee: {event_type} in {zone_id}, mood={scene.mood}, "
            f"press={len(scene.press_headlines)}, leader={scene.leader_dialogue is not None}"
        )
        return scene

    # =========================================================================
    # NARRATIVE GENERATION
    # =========================================================================

    async def _generate_narrative(
        self,
        event_type: str,
        zone_fr: str,
        effects: Dict,
        context: Dict,
        actor_country: str,
        player_caused: bool,
    ) -> str:
        """Genere le recit principal - AI ou templates"""

        # Fallback: templates statiques
        templates = NARRATIVE_TEMPLATES.get(event_type, NARRATIVE_TEMPLATES["default"])
        template = random.choice(templates)

        actor_name = WORLD_LEADERS.get(actor_country, {}).get("name", actor_country)

        narrative = template.format(
            zone_fr=zone_fr,
            defcon=context.get("defcon", 4),
            year=context.get("year", 1962),
            actor=actor_name,
        )

        return narrative

    # =========================================================================
    # LEADER DIALOGUES
    # =========================================================================

    async def _get_leader_dialogue(
        self,
        event_type: str,
        effects: Dict,
        context: Dict,
        player_caused: bool,
        actor_country: str,
        target_countries: List[str],
    ) -> Optional[LeaderDialogue]:
        """
        Genere un dialogue de leader.
        Utilise AIAdvisor.generate_diplomatic_response() si disponible.
        """

        # Determiner qui parle
        if player_caused:
            # Le joueur a agi -> l'adversaire reagit
            speaking_country = "USSR" if actor_country == "USA" else "USA"
        else:
            # Choisir le pays le plus pertinent
            if target_countries:
                speaking_country = target_countries[0]
            else:
                speaking_country = random.choice(["USSR", "FRA", "GBR", "CHN"])

        leader_info = WORLD_LEADERS.get(speaking_country, {
            "name": f"Le dirigeant de {speaking_country}",
            "title": "Chef d'Etat",
            "style": "neutral"
        })

        # Determiner le ton
        tone = self._determine_tone(event_type, effects, player_caused, speaking_country)

        # Generer le message (AI ou templates)
        message = self._generate_leader_message(
            speaking_country, tone, event_type, leader_info.get("style", "neutral")
        )

        return LeaderDialogue(
            speaker=leader_info.get("name", "Leader"),
            title=leader_info.get("title", "Chef d'Etat"),
            tone=tone,
            message=message,
            country=speaking_country,
            portrait_style="cold_war",
        )

    def _generate_leader_message(
        self, country: str, tone: str, event_type: str, style: str
    ) -> str:
        """Genere un message de leader base sur templates"""

        messages = {
            "USSR": {
                "angry": [
                    "Les imperialistes testent notre patience. Ils le regretteront!",
                    "Cette provocation ne restera pas sans reponse. Le monde socialiste est uni!",
                    "L'Amerique joue avec le feu. L'Union Sovietique ne reculera pas!",
                ],
                "threatening": [
                    "Si les Americains persistent, nous serons contraints d'agir. Les consequences seront terribles.",
                    "Nous avons les moyens de nous defendre. Que Washington s'en souvienne.",
                    "La puissance sovietique n'est pas un vain mot. Nous le prouverons si necessaire.",
                ],
                "pleased": [
                    "Voila une decision sage. La cooperation est toujours preferable a la confrontation.",
                    "L'Union Sovietique salue ce geste. La paix mondiale en sort renforcee.",
                ],
                "neutral": [
                    "Nous observons les developpements avec attention. L'URSS reste vigilante.",
                    "Moscou etudie la situation. Notre reponse sera mesuree mais ferme.",
                ],
            },
            "USA": {
                "angry": [
                    "Cette agression ne peut rester sans reponse. L'Amerique protegera ses interets!",
                    "Nous ne tolererons pas cette menace. Les Etats-Unis sont determines.",
                ],
                "threatening": [
                    "Que nos adversaires comprennent bien: nous n'hesiterons pas.",
                    "L'arsenal americain n'est pas une decoration. Nous sommes prets a l'utiliser.",
                ],
                "pleased": [
                    "C'est une victoire pour le monde libre. La democratie triomphe.",
                    "L'Amerique se rejouit de ce developpement positif.",
                ],
                "neutral": [
                    "Les Etats-Unis suivent la situation de pres. Nous restons engages pour la paix.",
                    "Nous consultons nos allies. La reponse sera coordonnee.",
                ],
            },
            "FRA": {
                "angry": [
                    "La France ne saurait accepter cette situation. Notre voix doit etre entendue!",
                    "Inacceptable! La France a son mot a dire dans les affaires du monde.",
                ],
                "neutral": [
                    "La France observe avec attention. Notre position independante est connue.",
                    "Nous restons attentifs. L'Europe doit avoir sa propre voix.",
                ],
                "pleased": [
                    "La France salue cette evolution. C'est un pas vers l'equilibre mondial.",
                ],
            },
        }

        country_messages = messages.get(country, messages.get("USA"))
        tone_messages = country_messages.get(tone, country_messages.get("neutral", ["..."]))
        return random.choice(tone_messages)

    def _determine_tone(
        self, event_type: str, effects: Dict, player_caused: bool, speaking_country: str
    ) -> str:
        """Determine le ton du dialogue"""
        aggressive_types = ["MIL", "BLOCKADE", "THREAT", "COUP", "DESTAB", "ASSASSIN", "PROXY"]
        if any(t in event_type for t in aggressive_types):
            return random.choice(["angry", "threatening"])

        positive_types = ["ALLIANCE", "SUMMIT", "TRADE", "AID", "NEGOTIATE"]
        if any(t in event_type for t in positive_types):
            return "pleased"

        return "neutral"

    def _needs_leader_reaction(
        self, event_type: str, importance: str, effects: Dict, defcon: int
    ) -> bool:
        """Un leader doit-il reagir?"""
        high_impact = ["MIL", "DIPLO", "crisis", "war", "treaty", "COUP", "BLOCKADE"]
        return (
            importance in ["major", "critical"]
            or defcon <= 2
            or any(t in event_type for t in high_impact)
        )

    # =========================================================================
    # PRESS HEADLINES (40+ SOURCES!)
    # =========================================================================

    async def _get_press_headlines(
        self,
        event_type: str,
        zone_fr: str,
        effects: Dict,
        context: Dict,
        actor_country: str,
    ) -> List[PressHeadline]:
        """
        Genere des perspectives presse MULTIPLES.
        Utilise les 40+ sources de media_sources.py!
        """
        headlines = []

        # Determiner le sentiment global
        stability_change = effects.get("stability", 0)
        influence_change = effects.get("influence_us", effects.get("influence", 0))

        if isinstance(influence_change, (int, float)) and influence_change > 5:
            sentiment = "positive"
        elif isinstance(stability_change, (int, float)) and stability_change < -10:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        if self._has_media_sources:
            # Utiliser les vraies sources avec biais contrastes!
            contrasting_sources = self._get_contrasting_sources(event_type)

            for source in contrasting_sources[:3]:  # 3 perspectives differentes
                headline = self._generate_headline_for_source(
                    source, event_type, zone_fr, sentiment, actor_country
                )
                headlines.append(headline)
        else:
            # Fallback: sources simples
            headlines.append(self._generate_simple_headline("nyt", "positive", zone_fr))
            headlines.append(self._generate_simple_headline("pravda", "negative", zone_fr))

        return headlines

    def _generate_headline_for_source(
        self,
        source: Dict,
        event_type: str,
        zone_fr: str,
        sentiment: str,
        actor_country: str,
    ) -> PressHeadline:
        """Genere un headline adapte au biais de la source"""

        source_id = source.get("id", "unknown")
        source_name = source.get("name", "Unknown")
        bias = source.get("bias", "neutral")
        country = source.get("country", "INT")
        credibility = source.get("credibility", "medium")

        # Ajuster le sentiment selon le biais
        adjusted_sentiment = self._adjust_sentiment_for_bias(
            sentiment, bias, actor_country
        )

        # Generer headline et excerpt selon biais
        headline, excerpt = self._generate_biased_content(
            bias, event_type, zone_fr, adjusted_sentiment, actor_country
        )

        return PressHeadline(
            source=source_name,
            source_id=source_id,
            headline=headline,
            excerpt=excerpt,
            sentiment=adjusted_sentiment,
            bias=bias,
            country=country,
            credibility=credibility,
        )

    def _adjust_sentiment_for_bias(
        self, base_sentiment: str, bias: str, actor_country: str
    ) -> str:
        """Ajuste le sentiment selon le biais de la source"""
        western_countries = {"USA", "GBR", "FRA", "DEU"}
        eastern_countries = {"USSR", "CHN", "CUB"}

        if bias == "pro_west":
            if actor_country in western_countries:
                return "positive" if base_sentiment != "negative" else "neutral"
            elif actor_country in eastern_countries:
                return "negative"

        elif bias == "pro_east":
            if actor_country in eastern_countries:
                return "positive" if base_sentiment != "negative" else "neutral"
            elif actor_country in western_countries:
                return "negative"

        return base_sentiment

    def _generate_biased_content(
        self,
        bias: str,
        event_type: str,
        zone_fr: str,
        sentiment: str,
        actor_country: str,
    ) -> tuple[str, str]:
        """Genere headline et excerpt avec biais editorial"""

        templates = {
            "pro_west": {
                "positive": (
                    f"Victoire de la liberte en {zone_fr}",
                    "Les forces democratiques progressent. Le monde libre salue cette avancee historique."
                ),
                "negative": (
                    f"L'ombre de la tyrannie s'etend sur {zone_fr}",
                    "Les experts s'inquietent de l'expansion du bloc communiste dans la region."
                ),
                "neutral": (
                    f"Developpements en {zone_fr}",
                    "Washington analyse la situation avec attention."
                ),
            },
            "pro_east": {
                "positive": (
                    f"Victoire du socialisme en {zone_fr}",
                    "Les peuples opprimés se liberent du joug imperialiste."
                ),
                "negative": (
                    f"Provocation imperialiste en {zone_fr}",
                    "Washington poursuit sa politique d'agression contre les peuples libres."
                ),
                "neutral": (
                    f"Situation en {zone_fr}",
                    "Moscou observe les developpements avec vigilance."
                ),
            },
            "neutral": {
                "positive": (
                    f"Avancees en {zone_fr}",
                    "Les analystes notent une evolution favorable de la situation."
                ),
                "negative": (
                    f"Tensions croissantes en {zone_fr}",
                    "La communaute internationale s'inquiete des derniers developpements."
                ),
                "neutral": (
                    f"Situation en evolution en {zone_fr}",
                    "Les observateurs attendent la suite des evenements."
                ),
            },
        }

        bias_templates = templates.get(bias, templates["neutral"])
        content = bias_templates.get(sentiment, bias_templates["neutral"])
        return content

    def _generate_simple_headline(
        self, source_id: str, sentiment: str, zone_fr: str
    ) -> PressHeadline:
        """Fallback: headline simple"""
        return PressHeadline(
            source="Press Agency",
            source_id=source_id,
            headline=f"Developpements en {zone_fr}",
            excerpt="La situation evolue dans la region.",
            sentiment=sentiment,
            bias="neutral",
            country="INT",
            credibility="medium",
        )

    def _is_public_event(self, event_type: str, importance: str) -> bool:
        """Evenement merite-t-il une couverture presse?"""
        return importance != "minor" and "COV" not in event_type

    # =========================================================================
    # INTEL REPORTS
    # =========================================================================

    def _get_intel_report(
        self, event_type: str, zone_fr: str, effects: Dict
    ) -> IntelReport:
        """Genere un rapport de renseignement"""

        # Classification selon importance
        if "COUP" in event_type or "ASSASSIN" in event_type:
            classification = "TOP SECRET - EYES ONLY"
            reliability = "uncertain"
        elif "SABOTAGE" in event_type:
            classification = "SECRET"
            reliability = "likely"
        else:
            classification = "CONFIDENTIAL"
            reliability = "likely"

        # Source type
        if "INTEL" in event_type:
            source_type = "sigint"
        elif "COV" in event_type:
            source_type = "humint"
        else:
            source_type = "imagery"

        # Contenu
        template = INTEL_TEMPLATES.get(event_type, INTEL_TEMPLATES["default"])
        content = template.format(zone_fr=zone_fr)

        # Note d'analyste pour operations critiques
        analyst_note = None
        if "COUP" in event_type:
            analyst_note = "ANALYSE: Succes de l'operation difficile a evaluer. Recommandons prudence maximale."
        elif "ASSASSIN" in event_type:
            analyst_note = "ANALYSE: Retombees politiques imprevisibles. Plausible deniability essentielle."

        return IntelReport(
            classification=classification,
            content=content,
            reliability=reliability,
            source_type=source_type,
            analyst_note=analyst_note,
        )

    def _is_covert_event(self, event_type: str) -> bool:
        """Evenement est-il secret?"""
        return "COV" in event_type or "INTEL" in event_type

    # =========================================================================
    # CAUSAL CONTEXT (Timeline Integration)
    # =========================================================================

    def _build_causal_context(
        self,
        event_type: str,
        zone_id: str,
        caused_by: str,
        effects_chain: List[Dict],
        timeline_event: "TimelineEvent",
        all_zones: Dict,
    ) -> CausalContext:
        """
        Construit le contexte causal.
        Utilise timeline.py et domino_effects.py
        """
        context = CausalContext()

        # 1. Cause de l'evenement
        if timeline_event and hasattr(timeline_event, "caused_by_chain"):
            if timeline_event.caused_by_chain:
                cause = timeline_event.caused_by_chain[0]
                context.caused_by = cause.title_fr
                context.caused_by_date = str(cause.date) if hasattr(cause, "date") else None

        elif caused_by:
            context.caused_by = caused_by

        # 2. Effets probables
        if timeline_event and hasattr(timeline_event, "effects_chain"):
            context.effects_preview = [
                e.title_fr for e in timeline_event.effects_chain[:3]
                if hasattr(e, "title_fr")
            ]
        elif effects_chain:
            context.effects_preview = [
                e.get("title_fr", e.get("title", "Consequence"))
                for e in effects_chain[:3]
            ]

        # 3. Zones adjacentes affectees (effet domino!)
        if self._has_domino and zone_id and all_zones:
            adjacent = self._adjacent_zones.get(zone_id, [])
            for adj_id in adjacent:
                adj_zone = all_zones.get(adj_id)
                if adj_zone:
                    # Zone adjacente en crise = effet domino
                    if hasattr(adj_zone, "has_crisis") and adj_zone.has_crisis:
                        context.domino_zones.append(ZONE_NAMES_FR.get(adj_id, adj_id))

        return context

    # =========================================================================
    # MOOD & TEASER
    # =========================================================================

    def _determine_mood(
        self, event_type: str, effects: Dict, context: Dict, defcon: int
    ) -> str:
        """Determine l'ambiance de la scene"""
        if defcon <= 2:
            return "dark"

        if "victory" in event_type.lower() or "success" in event_type.lower():
            return "triumphant"
        if "crisis" in event_type.lower() or "BLOCKADE" in event_type:
            return "tense"
        if "COUP" in event_type or "DESTAB" in event_type or "ASSASSIN" in event_type:
            return "dark"
        if "SUMMIT" in event_type or "ALLIANCE" in event_type:
            return "hopeful"

        stability_change = effects.get("stability", 0)
        if isinstance(stability_change, (int, float)) and stability_change < -15:
            return "tense"

        return "neutral"

    def _format_consequence_teaser(self, effects_chain: List[Dict]) -> Optional[str]:
        """Cree un teaser pour les consequences"""
        if not effects_chain:
            return None

        next_event = effects_chain[0]
        title = next_event.get("title_fr", next_event.get("title", "des consequences"))
        return f"Ceci pourrait mener a: {title}..."


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Instance globale
_orchestrator: Optional[NarrativeOrchestrator] = None


def get_orchestrator(
    ai_advisor: Optional["AIAdvisor"] = None,
    timeline: Optional["TimelineManager"] = None,
) -> NarrativeOrchestrator:
    """Retourne l'instance globale du NarrativeOrchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NarrativeOrchestrator(ai_advisor=ai_advisor, timeline=timeline)
    return _orchestrator


def set_orchestrator(orchestrator: NarrativeOrchestrator) -> None:
    """Definit l'instance globale du NarrativeOrchestrator"""
    global _orchestrator
    _orchestrator = orchestrator


async def compose_narrative_scene(
    event_type: str,
    zone_id: str = None,
    effects: Dict = None,
    context: Dict = None,
    caused_by: str = None,
    effects_chain: List[Dict] = None,
    importance: str = "normal",
    player_caused: bool = False,
    actor_country: str = "USA",
    target_countries: List[str] = None,
    timeline_event: "TimelineEvent" = None,
    all_zones: Dict = None,
) -> Dict:
    """
    Fonction de commodite pour composer une scene narrative.

    Retourne un dict pret a etre envoye au frontend.
    """
    orchestrator = get_orchestrator()
    scene = await orchestrator.compose_scene(
        event_type=event_type,
        zone_id=zone_id,
        effects=effects,
        context=context,
        caused_by=caused_by,
        effects_chain=effects_chain,
        importance=importance,
        player_caused=player_caused,
        actor_country=actor_country,
        target_countries=target_countries,
        timeline_event=timeline_event,
        all_zones=all_zones,
    )
    return scene.to_dict()
