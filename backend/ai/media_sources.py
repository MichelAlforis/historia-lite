"""Media Sources for Historia Lite - News outlets with editorial biases

Each media source has:
- name: Official name
- country: Origin country code
- region: Geographic region (west, east, middle_east, asia, global)
- bias: Editorial slant (pro_west, pro_east, neutral, pro_authoritarian, liberal, conservative, economic)
- style_fr: Writing style description in French
- tone: Default tone (formal, sensational, analytical, diplomatic)
- credibility: How "serious" the source is (high, medium, tabloid)
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import random


class MediaBias(str, Enum):
    """Editorial biases for media sources"""
    PRO_WEST = "pro_west"
    PRO_EAST = "pro_east"
    PRO_AUTHORITARIAN = "pro_authoritarian"
    NEUTRAL = "neutral"
    LIBERAL = "liberal"
    CONSERVATIVE = "conservative"
    ECONOMIC = "economic"
    SENSATIONALIST = "sensationalist"


class MediaRegion(str, Enum):
    """Geographic regions for media sources"""
    WEST = "west"
    EAST = "east"
    MIDDLE_EAST = "middle_east"
    ASIA = "asia"
    AFRICA = "africa"
    LATAM = "latam"
    GLOBAL = "global"


# Comprehensive media source definitions
MEDIA_SOURCES: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # WESTERN SOURCES
    # =========================================================================
    "reuters": {
        "name": "Reuters",
        "country": "GBR",
        "region": MediaRegion.GLOBAL,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Factuel, depouille, agence de presse internationale",
        "tone": "formal",
        "credibility": "high",
        "prompt_hint": "Style agence de presse, factuel et neutre, pas d'opinion",
    },
    "afp": {
        "name": "AFP",
        "country": "FRA",
        "region": MediaRegion.WEST,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Agence francaise, factuel avec sensibilite europeenne",
        "tone": "formal",
        "credibility": "high",
        "prompt_hint": "Style agence francaise, sobre et factuel",
    },
    "le_monde": {
        "name": "Le Monde",
        "country": "FRA",
        "region": MediaRegion.WEST,
        "bias": MediaBias.LIBERAL,
        "style_fr": "Analyse approfondie, perspective intellectuelle francaise",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Style editorialiste francais, analyse geopolitique nuancee, legere preference pour les valeurs democratiques",
    },
    "nyt": {
        "name": "The New York Times",
        "country": "USA",
        "region": MediaRegion.WEST,
        "bias": MediaBias.PRO_WEST,
        "style_fr": "Journal de reference americain, perspective atlantiste",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Perspective americaine mainstream, favorable aux interets occidentaux, critique des regimes autoritaires",
    },
    "wsj": {
        "name": "The Wall Street Journal",
        "country": "USA",
        "region": MediaRegion.WEST,
        "bias": MediaBias.ECONOMIC,
        "style_fr": "Focus economique et financier, conservateur fiscal",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Angle economique et marchés, impact sur les investissements, perspective business",
    },
    "guardian": {
        "name": "The Guardian",
        "country": "GBR",
        "region": MediaRegion.WEST,
        "bias": MediaBias.LIBERAL,
        "style_fr": "Progressiste, droits de l'homme, critique des pouvoirs",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Angle progressiste, attention aux droits de l'homme, critique des exces de pouvoir",
    },
    "der_spiegel": {
        "name": "Der Spiegel",
        "country": "DEU",
        "region": MediaRegion.WEST,
        "bias": MediaBias.LIBERAL,
        "style_fr": "Investigatif allemand, rigoureux et critique",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Style allemand rigoureux, investigatif, sans complaisance",
    },
    "economist": {
        "name": "The Economist",
        "country": "GBR",
        "region": MediaRegion.GLOBAL,
        "bias": MediaBias.ECONOMIC,
        "style_fr": "Analyse economique globale, liberal classique",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Analyse macro-economique, perspective liberale classique, ton sophistique",
    },
    "bbc": {
        "name": "BBC World",
        "country": "GBR",
        "region": MediaRegion.GLOBAL,
        "bias": MediaBias.PRO_WEST,
        "style_fr": "Service public britannique, equilibre apparent avec biais occidental subtil",
        "tone": "formal",
        "credibility": "high",
        "prompt_hint": "Ton BBC formel, apparence d'equilibre, perspective britannique sous-jacente",
    },
    "fox_news": {
        "name": "Fox News",
        "country": "USA",
        "region": MediaRegion.WEST,
        "bias": MediaBias.CONSERVATIVE,
        "style_fr": "Conservateur americain, patriotique, anti-establishment",
        "tone": "sensational",
        "credibility": "medium",
        "prompt_hint": "Perspective conservatrice americaine, patriotique, critique des elites, ton affirmatif",
    },
    "daily_mail": {
        "name": "Daily Mail",
        "country": "GBR",
        "region": MediaRegion.WEST,
        "bias": MediaBias.SENSATIONALIST,
        "style_fr": "Tabloide britannique, sensationnel, populiste",
        "tone": "sensational",
        "credibility": "tabloid",
        "prompt_hint": "Style tabloide, titres accrocheurs, angle emotionnel, simplification",
    },

    # =========================================================================
    # EASTERN / RUSSIAN SOURCES
    # =========================================================================
    "rt": {
        "name": "RT (Russia Today)",
        "country": "RUS",
        "region": MediaRegion.EAST,
        "bias": MediaBias.PRO_EAST,
        "style_fr": "Media d'Etat russe, contre-narratif occidental",
        "tone": "diplomatic",
        "credibility": "medium",
        "prompt_hint": "Perspective russe officielle, critique de l'Occident, defense des interets russes, ton 'alternatif'",
    },
    "tass": {
        "name": "TASS",
        "country": "RUS",
        "region": MediaRegion.EAST,
        "bias": MediaBias.PRO_AUTHORITARIAN,
        "style_fr": "Agence d'Etat russe, ligne officielle du Kremlin",
        "tone": "formal",
        "credibility": "medium",
        "prompt_hint": "Voix officielle russe, defense des positions de Moscou, ton diplomatique mais ferme",
    },
    "sputnik": {
        "name": "Sputnik",
        "country": "RUS",
        "region": MediaRegion.EAST,
        "bias": MediaBias.PRO_EAST,
        "style_fr": "Media russe international, narratif alternatif",
        "tone": "analytical",
        "credibility": "medium",
        "prompt_hint": "Contre-narratif aux medias occidentaux, critique de l'OTAN et de l'UE, defense multipolaire",
    },

    # =========================================================================
    # CHINESE SOURCES
    # =========================================================================
    "xinhua": {
        "name": "Xinhua",
        "country": "CHN",
        "region": MediaRegion.ASIA,
        "bias": MediaBias.PRO_AUTHORITARIAN,
        "style_fr": "Agence d'Etat chinoise, ligne officielle de Pekin",
        "tone": "formal",
        "credibility": "medium",
        "prompt_hint": "Position officielle chinoise, defense de la souverainete, critique de l'ingerence occidentale",
    },
    "global_times": {
        "name": "Global Times",
        "country": "CHN",
        "region": MediaRegion.ASIA,
        "bias": MediaBias.PRO_AUTHORITARIAN,
        "style_fr": "Tabloide nationaliste chinois, ton assertif",
        "tone": "sensational",
        "credibility": "medium",
        "prompt_hint": "Nationalisme chinois, ton combatif, critique virulente de l'Occident, defense musclée des interets chinois",
    },
    "scmp": {
        "name": "South China Morning Post",
        "country": "HKG",
        "region": MediaRegion.ASIA,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Journal de Hong Kong, equilibre Chine-Occident",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Perspective asiatique equilibree, pont entre Chine et Occident, analyse nuancee",
    },

    # =========================================================================
    # MIDDLE EASTERN SOURCES
    # =========================================================================
    "al_jazeera": {
        "name": "Al Jazeera",
        "country": "QAT",
        "region": MediaRegion.MIDDLE_EAST,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Perspective arabe internationale, voix du Sud global",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Perspective monde arabe, critique des politiques occidentales au Moyen-Orient, voix des pays du Sud",
    },
    "al_arabiya": {
        "name": "Al Arabiya",
        "country": "SAU",
        "region": MediaRegion.MIDDLE_EAST,
        "bias": MediaBias.PRO_WEST,
        "style_fr": "Perspective saoudienne, pro-occidental au Moyen-Orient",
        "tone": "formal",
        "credibility": "medium",
        "prompt_hint": "Ligne editoriale saoudienne, critique de l'Iran, alignement modere avec l'Occident",
    },
    "press_tv": {
        "name": "Press TV",
        "country": "IRN",
        "region": MediaRegion.MIDDLE_EAST,
        "bias": MediaBias.PRO_AUTHORITARIAN,
        "style_fr": "Media d'Etat iranien, anti-occidental",
        "tone": "diplomatic",
        "credibility": "medium",
        "prompt_hint": "Perspective iranienne officielle, anti-americaine, defense de l'axe de resistance",
    },
    "times_of_israel": {
        "name": "Times of Israel",
        "country": "ISR",
        "region": MediaRegion.MIDDLE_EAST,
        "bias": MediaBias.PRO_WEST,
        "style_fr": "Perspective israelienne, focus securite regionale",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Perspective israelienne, focus sur la securite, analyse des menaces regionales",
    },

    # =========================================================================
    # ASIAN SOURCES
    # =========================================================================
    "nikkei": {
        "name": "Nikkei Asia",
        "country": "JPN",
        "region": MediaRegion.ASIA,
        "bias": MediaBias.ECONOMIC,
        "style_fr": "Reference economique asiatique, analyse marches",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Angle economique asiatique, impact sur les marches, perspective japonaise pro-business",
    },
    "straits_times": {
        "name": "The Straits Times",
        "country": "SGP",
        "region": MediaRegion.ASIA,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Reference de Singapour, pragmatique et equilibre",
        "tone": "formal",
        "credibility": "high",
        "prompt_hint": "Perspective singapourienne pragmatique, equilibre entre grandes puissances, focus stabilite",
    },
    "times_of_india": {
        "name": "Times of India",
        "country": "IND",
        "region": MediaRegion.ASIA,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Grand quotidien indien, perspective Non-Alignes",
        "tone": "formal",
        "credibility": "high",
        "prompt_hint": "Perspective indienne, heritage Non-Alignes, equilibre entre Occident et Russie/Chine",
    },

    # =========================================================================
    # AFRICAN SOURCES
    # =========================================================================
    "africa_news": {
        "name": "Africanews",
        "country": "COG",
        "region": MediaRegion.AFRICA,
        "bias": MediaBias.NEUTRAL,
        "style_fr": "Perspective panafricaine, voix du continent",
        "tone": "formal",
        "credibility": "medium",
        "prompt_hint": "Perspective africaine, critique du neocolonialisme, focus developpement continental",
    },

    # =========================================================================
    # LATIN AMERICAN SOURCES
    # =========================================================================
    "telesur": {
        "name": "TeleSUR",
        "country": "VEN",
        "region": MediaRegion.LATAM,
        "bias": MediaBias.PRO_EAST,
        "style_fr": "Media bolivarien, anti-imperialiste",
        "tone": "analytical",
        "credibility": "medium",
        "prompt_hint": "Perspective bolivarienne, anti-imperialisme americain, solidarite Sud-Sud",
    },
    "folha": {
        "name": "Folha de S.Paulo",
        "country": "BRA",
        "region": MediaRegion.LATAM,
        "bias": MediaBias.LIBERAL,
        "style_fr": "Grand quotidien bresilien, liberal progressiste",
        "tone": "analytical",
        "credibility": "high",
        "prompt_hint": "Perspective bresilienne, puissance emergente, critique mais pragmatique",
    },
}


def get_media_source(source_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific media source by ID"""
    source = MEDIA_SOURCES.get(source_id)
    if source:
        return {"id": source_id, **source}
    return None


def get_sources_by_region(region: str) -> List[Dict[str, Any]]:
    """Get all media sources from a specific region"""
    return [
        {"id": sid, **source}
        for sid, source in MEDIA_SOURCES.items()
        if source.get("region") == region or source.get("region") == MediaRegion.GLOBAL
    ]


def get_sources_by_bias(bias: str) -> List[Dict[str, Any]]:
    """Get all media sources with a specific bias"""
    return [
        {"id": sid, **source}
        for sid, source in MEDIA_SOURCES.items()
        if source.get("bias") == bias
    ]


def get_random_source(
    region: str = None,
    bias: str = None,
    exclude_tabloids: bool = False
) -> Dict[str, Any]:
    """Get a random media source, optionally filtered"""
    candidates = []

    for sid, source in MEDIA_SOURCES.items():
        # Filter by region
        if region and source.get("region") != region and source.get("region") != MediaRegion.GLOBAL:
            continue
        # Filter by bias
        if bias and source.get("bias") != bias:
            continue
        # Filter out tabloids
        if exclude_tabloids and source.get("credibility") == "tabloid":
            continue
        candidates.append({"id": sid, **source})

    if not candidates:
        # Fallback to any source
        sid = random.choice(list(MEDIA_SOURCES.keys()))
        return {"id": sid, **MEDIA_SOURCES[sid]}

    return random.choice(candidates)


def get_contrasting_sources(event_type: str = None) -> List[Dict[str, Any]]:
    """Get 2-3 contrasting sources for balanced/dramatic coverage

    Returns sources with different biases to show multiple perspectives
    """
    # Define contrasting pairs
    contrasts = [
        (MediaBias.PRO_WEST, MediaBias.PRO_EAST),
        (MediaBias.PRO_WEST, MediaBias.PRO_AUTHORITARIAN),
        (MediaBias.LIBERAL, MediaBias.CONSERVATIVE),
    ]

    # Pick a contrast type
    bias_a, bias_b = random.choice(contrasts)

    sources_a = get_sources_by_bias(bias_a)
    sources_b = get_sources_by_bias(bias_b)
    neutral_sources = get_sources_by_bias(MediaBias.NEUTRAL)

    result = []
    if sources_a:
        result.append(random.choice(sources_a))
    if sources_b:
        result.append(random.choice(sources_b))
    if neutral_sources and len(result) < 3:
        result.append(random.choice(neutral_sources))

    return result


def select_source_for_event(
    player_country: str,
    event_sentiment: str,  # positive, negative, neutral
    event_type: str = None  # war, economy, diplomacy, etc.
) -> Dict[str, Any]:
    """Intelligently select a media source based on event context

    Args:
        player_country: Country code of player
        event_sentiment: How the event portrays the player
        event_type: Type of event for context

    Returns:
        A media source that would realistically cover this event
    """
    # Determine player's geopolitical alignment
    western_countries = {"USA", "GBR", "FRA", "DEU", "CAN", "ITA", "ESP", "JPN", "KOR", "AUS"}
    eastern_countries = {"RUS", "CHN", "BLR", "IRN", "PRK", "SYR", "VEN", "CUB"}

    is_western = player_country in western_countries
    is_eastern = player_country in eastern_countries

    # Select appropriate sources based on sentiment and alignment
    if event_sentiment == "positive":
        if is_western:
            # Western positive news: Western sources will cover favorably
            candidates = get_sources_by_bias(MediaBias.PRO_WEST) + get_sources_by_bias(MediaBias.LIBERAL)
        elif is_eastern:
            # Eastern positive news: Eastern sources will cover favorably
            candidates = get_sources_by_bias(MediaBias.PRO_EAST) + get_sources_by_bias(MediaBias.PRO_AUTHORITARIAN)
        else:
            # Neutral country: Any source
            candidates = get_sources_by_bias(MediaBias.NEUTRAL)

    elif event_sentiment == "negative":
        if is_western:
            # Western negative news: Eastern/critical sources will jump on it
            candidates = get_sources_by_bias(MediaBias.PRO_EAST) + get_sources_by_bias(MediaBias.SENSATIONALIST)
        elif is_eastern:
            # Eastern negative news: Western sources will report critically
            candidates = get_sources_by_bias(MediaBias.PRO_WEST) + get_sources_by_bias(MediaBias.LIBERAL)
        else:
            candidates = get_sources_by_bias(MediaBias.NEUTRAL)

    else:
        # Neutral events: Favor analytical sources
        candidates = [
            s for s in get_sources_by_bias(MediaBias.NEUTRAL)
            if s.get("tone") == "analytical"
        ]
        if not candidates:
            candidates = get_sources_by_bias(MediaBias.NEUTRAL)

    # Add some economic sources for economic events
    if event_type in ("economy", "trade", "sanctions", "debt"):
        candidates.extend(get_sources_by_bias(MediaBias.ECONOMIC))

    # Fallback
    if not candidates:
        return get_random_source(exclude_tabloids=True)

    return random.choice(candidates)


def get_source_prompt_enhancement(source: Dict[str, Any]) -> str:
    """Generate prompt enhancement based on source characteristics"""

    parts = []

    # Source identity
    parts.append(f"Tu es un journaliste de {source['name']} ({source.get('country', 'International')}).")

    # Style hint
    if source.get("style_fr"):
        parts.append(f"Style: {source['style_fr']}.")

    # Bias hint
    if source.get("prompt_hint"):
        parts.append(source["prompt_hint"])

    # Tone
    tone_hints = {
        "formal": "Ton formel et professionnel.",
        "analytical": "Ton analytique et reflechi.",
        "sensational": "Ton accrocheur et emotionnel.",
        "diplomatic": "Ton diplomatique et mesure.",
    }
    if source.get("tone") in tone_hints:
        parts.append(tone_hints[source["tone"]])

    return " ".join(parts)


def get_all_sources_summary() -> List[Dict[str, str]]:
    """Get a summary of all sources for frontend display"""
    return [
        {
            "id": sid,
            "name": source["name"],
            "country": source.get("country", ""),
            "region": source.get("region", ""),
            "bias": source.get("bias", ""),
            "credibility": source.get("credibility", "medium"),
        }
        for sid, source in MEDIA_SOURCES.items()
    ]
