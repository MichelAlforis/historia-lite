"""Social reactions system for projects with sensitive tags

Handles:
- Internal reactions (stability, rebellions) based on country's social profile
- External reactions (diplomatic relations) from neighbors and ideological opponents
"""
import logging
from typing import TYPE_CHECKING, Dict, List, Tuple

from schemas.interaction import (
    ActiveProject,
    ProjectTemplate,
    SocialTag,
)
from engine.events import Event

if TYPE_CHECKING:
    from engine.world import World
    from engine.country import Country

logger = logging.getLogger(__name__)


# Countries with strong reactions to specific tags
# Maps SocialTag -> list of (country_id, reaction_strength)
IDEOLOGICAL_OPPONENTS: Dict[SocialTag, List[Tuple[str, int]]] = {
    SocialTag.LGBTQ_RIGHTS: [
        ("IRN", -30),   # Iran - strong opposition
        ("SAU", -25),   # Saudi Arabia - strong opposition
        ("PAK", -20),   # Pakistan - opposition
        ("EGY", -15),   # Egypt - moderate opposition
        ("RUS", -15),   # Russia - moderate opposition
        ("TUR", -10),   # Turkey - mild opposition
    ],
    SocialTag.WOMEN_RIGHTS: [
        ("IRN", -25),
        ("SAU", -20),
        ("PAK", -15),
    ],
    SocialTag.SECULAR: [
        ("IRN", -20),
        ("SAU", -15),
        ("ISR", -5),    # Israel - complicated relationship with secularism
    ],
    SocialTag.RELIGIOUS: [
        ("FRA", -10),   # France - strong secularism
        ("CHN", -10),   # China - state atheism
    ],
    SocialTag.PROGRESSIVE: [
        ("IRN", -15),
        ("SAU", -15),
        ("RUS", -10),
        ("CHN", -5),
    ],
    SocialTag.CONSERVATIVE: [
        ("SWE", -5),    # Progressive countries may dislike
        ("NLD", -5),
    ],
    SocialTag.NATIONALIST: [
        ("DEU", -10),   # Germany wary of nationalism
        ("EU", -5),     # EU bloc preference for integration
    ],
    SocialTag.MILITARY_BUILDUP: [
        # Neighbors concerned - handled dynamically
    ],
    SocialTag.IMMIGRATION: [
        ("POL", -10),   # Eastern European opposition
        ("HUN", -10),   # Hungary - strong opposition
    ],
}

# Countries that support certain progressive policies
IDEOLOGICAL_SUPPORTERS: Dict[SocialTag, List[Tuple[str, int]]] = {
    SocialTag.LGBTQ_RIGHTS: [
        ("NLD", +10),   # Netherlands - strong support
        ("SWE", +10),   # Sweden - strong support
        ("CAN", +8),    # Canada - support
        ("DEU", +5),    # Germany - support
        ("FRA", +5),    # France - support
    ],
    SocialTag.WOMEN_RIGHTS: [
        ("SWE", +10),
        ("NLD", +8),
        ("CAN", +8),
        ("FRA", +5),
        ("DEU", +5),
    ],
    SocialTag.ENVIRONMENTAL: [
        ("SWE", +10),
        ("DEU", +8),
        ("NLD", +5),
        ("FRA", +5),
    ],
    SocialTag.SECULAR: [
        ("FRA", +10),   # France - strong secular tradition
        ("TUR", +5),    # Turkey - secular tradition (Ataturk)
    ],
}


def calculate_internal_reaction(
    project: "ProjectTemplate",
    country: "Country"
) -> Tuple[int, str]:
    """
    Calculate internal stability impact of a project.

    Returns (stability_delta, reason_fr)

    Example: Muslim country starting LGBTQ_RIGHTS project -> major instability
    """
    if not project.social_tags:
        return 0, ""

    stability_delta = 0
    reasons = []

    profile = country.social_profile

    for tag in project.social_tags:
        # LGBTQ rights in conservative/religious countries
        if tag == SocialTag.LGBTQ_RIGHTS:
            if profile.religion == "muslim" and profile.religiosity > 60:
                stability_delta -= 25
                reasons.append("Opposition religieuse au mariage pour tous")
            elif profile.conservatism > 70:
                stability_delta -= 15
                reasons.append("Resistance conservatrice")
            elif profile.religion == "orthodox" and profile.religiosity > 50:
                stability_delta -= 12
                reasons.append("Opposition orthodoxe")
            elif profile.conservatism > 50:
                stability_delta -= 5
                reasons.append("Resistance moderee")

        # Women's rights in conservative countries
        elif tag == SocialTag.WOMEN_RIGHTS:
            if profile.religion == "muslim" and profile.conservatism > 70:
                stability_delta -= 20
                reasons.append("Opposition aux droits des femmes")
            elif profile.conservatism > 60:
                stability_delta -= 10
                reasons.append("Resistance traditionaliste")

        # Secular policies in religious countries
        elif tag == SocialTag.SECULAR:
            if profile.religiosity > 70:
                stability_delta -= 15
                reasons.append("Opposition religieuse a la laicite")
            elif profile.religiosity > 50:
                stability_delta -= 8
                reasons.append("Tensions laiques")

        # Religious policies in secular countries
        elif tag == SocialTag.RELIGIOUS:
            if profile.religion == "secular" or profile.religiosity < 30:
                stability_delta -= 10
                reasons.append("Opposition laique")

        # Progressive policies in conservative countries
        elif tag == SocialTag.PROGRESSIVE:
            if profile.conservatism > 70:
                stability_delta -= 12
                reasons.append("Resistance aux reformes progressistes")
            elif profile.conservatism > 50:
                stability_delta -= 5
                reasons.append("Resistance moderee aux reformes")

        # Conservative policies in progressive countries
        elif tag == SocialTag.CONSERVATIVE:
            if profile.conservatism < 30:
                stability_delta -= 8
                reasons.append("Opposition progressiste")

        # Nationalist policies
        elif tag == SocialTag.NATIONALIST:
            if profile.nationalism < 30:
                stability_delta -= 5
                reasons.append("Opposition au nationalisme")
            elif profile.nationalism > 70:
                stability_delta += 5  # Popular with nationalists
                reasons.append("Soutien nationaliste")

        # Immigration policies in nationalist countries
        elif tag == SocialTag.IMMIGRATION:
            if profile.nationalism > 60:
                stability_delta -= 15
                reasons.append("Opposition a l'immigration")
            elif profile.nationalism > 40:
                stability_delta -= 8
                reasons.append("Tensions sur l'immigration")

    reason_text = ", ".join(reasons) if reasons else ""
    return stability_delta, reason_text


def calculate_external_reactions(
    project: "ProjectTemplate",
    country: "Country",
    world: "World"
) -> List[Tuple[str, int, str]]:
    """
    Calculate diplomatic reactions from other countries.

    Returns list of (other_country_id, relation_delta, reason_fr)

    Example: Iran reacts negatively if neighbor starts LGBTQ_RIGHTS project
    """
    reactions = []

    if not project.social_tags:
        return reactions

    for tag in project.social_tags:
        # Check ideological opponents
        if tag in IDEOLOGICAL_OPPONENTS:
            for opponent_id, base_reaction in IDEOLOGICAL_OPPONENTS[tag]:
                opponent = world.get_country(opponent_id)
                if not opponent:
                    continue

                # Reaction is stronger for neighbors
                is_neighbor = (
                    opponent_id in getattr(country, 'neighbors', []) or
                    country.id in getattr(opponent, 'neighbors', [])
                )
                multiplier = 1.5 if is_neighbor else 1.0

                # Adjust based on existing relations
                existing_rel = country.get_relation(opponent_id)
                if existing_rel < -50:
                    multiplier *= 1.2  # Already hostile, reaction stronger

                final_reaction = int(base_reaction * multiplier)

                if final_reaction != 0:
                    reason = f"{opponent.name_fr} desapprouve ce projet"
                    reactions.append((opponent_id, final_reaction, reason))

        # Check ideological supporters
        if tag in IDEOLOGICAL_SUPPORTERS:
            for supporter_id, base_reaction in IDEOLOGICAL_SUPPORTERS[tag]:
                supporter = world.get_country(supporter_id)
                if not supporter or supporter_id == country.id:
                    continue

                final_reaction = base_reaction

                if final_reaction != 0:
                    reason = f"{supporter.name_fr} salue cette initiative"
                    reactions.append((supporter_id, final_reaction, reason))

        # Military buildup concerns neighbors
        if tag == SocialTag.MILITARY_BUILDUP:
            neighbors = getattr(country, 'neighbors', [])
            for neighbor_id in neighbors:
                neighbor = world.get_country(neighbor_id)
                if not neighbor:
                    continue

                # Rivals are more concerned
                base_reaction = -15 if country.is_rival(neighbor_id) else -5
                reason = f"{neighbor.name_fr} s'inquiete du renforcement militaire"
                reactions.append((neighbor_id, base_reaction, reason))

    return reactions


def apply_project_social_effects(
    project: "ProjectTemplate",
    country: "Country",
    world: "World"
) -> List[Event]:
    """
    Apply social effects when a project is started.

    Returns list of events generated by social reactions.
    """
    events = []

    # Calculate internal reaction
    stability_delta, internal_reason = calculate_internal_reaction(project, country)

    if stability_delta != 0:
        # Apply stability change
        old_stability = country.stability
        country.stability = max(0, min(100, country.stability + stability_delta))

        # Generate event
        if stability_delta < -15:
            event = Event(
                id=f"social_unrest_{world.year}_{country.id}_{project.id}",
                year=world.year,
                type="negative",
                title="Social Unrest",
                title_fr="Troubles sociaux",
                description=f"{project.name} causes significant social unrest in {country.name}",
                description_fr=f"{project.name_fr} provoque des troubles sociaux importants. {internal_reason}",
                country_id=country.id
            )
            events.append(event)
            logger.info(f"{country.id}: Project {project.id} caused stability {stability_delta} ({internal_reason})")
        elif stability_delta < -5:
            event = Event(
                id=f"social_tension_{world.year}_{country.id}_{project.id}",
                year=world.year,
                type="warning",
                title="Social Tensions",
                title_fr="Tensions sociales",
                description=f"{project.name} causes tensions in {country.name}",
                description_fr=f"{project.name_fr} cree des tensions. {internal_reason}",
                country_id=country.id
            )
            events.append(event)

    # Calculate external reactions
    external_reactions = calculate_external_reactions(project, country, world)

    for other_id, relation_delta, reason in external_reactions:
        if relation_delta != 0:
            # Apply relation change
            country.modify_relation(other_id, relation_delta)

            other = world.get_country(other_id)
            if other:
                other.modify_relation(country.id, relation_delta)

            # Generate events for significant reactions
            if relation_delta <= -15:
                event = Event(
                    id=f"diplomatic_protest_{world.year}_{country.id}_{other_id}",
                    year=world.year,
                    type="diplomatic",
                    title="Diplomatic Protest",
                    title_fr="Protestation diplomatique",
                    description=f"{other.name if other else other_id} protests {country.name}'s {project.name}",
                    description_fr=f"{reason}. Relations: {relation_delta}",
                    country_id=country.id
                )
                events.append(event)
            elif relation_delta >= 10:
                event = Event(
                    id=f"diplomatic_support_{world.year}_{country.id}_{other_id}",
                    year=world.year,
                    type="positive",
                    title="Diplomatic Support",
                    title_fr="Soutien diplomatique",
                    description=f"{other.name if other else other_id} supports {country.name}'s {project.name}",
                    description_fr=f"{reason}. Relations: +{relation_delta}",
                    country_id=country.id
                )
                events.append(event)

    return events


def detect_social_tags_from_description(description: str) -> List[SocialTag]:
    """
    Auto-detect social tags from project description.
    Used by AI suggestion endpoint.
    """
    description_lower = description.lower()
    tags = []

    # LGBTQ rights keywords
    lgbtq_keywords = [
        "mariage pour tous", "same-sex", "homosex", "lgbtq", "lgbt", "gay",
        "mariage homosexuel", "union civile", "pride", "gender identity"
    ]
    if any(kw in description_lower for kw in lgbtq_keywords):
        tags.append(SocialTag.LGBTQ_RIGHTS)

    # Women's rights keywords
    women_keywords = [
        "feminic", "femme", "women", "abortion", "avortement", "egalite des sexes",
        "gender equality", "ivg", "droit des femmes", "parite"
    ]
    if any(kw in description_lower for kw in women_keywords):
        tags.append(SocialTag.WOMEN_RIGHTS)

    # Secular keywords
    secular_keywords = [
        "laicit", "secular", "separation eglise", "separation church",
        "non-religious", "etat laic"
    ]
    if any(kw in description_lower for kw in secular_keywords):
        tags.append(SocialTag.SECULAR)

    # Religious keywords
    religious_keywords = [
        "religious", "religieu", "church", "mosque", "eglise", "mosquee",
        "faith-based", "spirituel", "charia", "sharia"
    ]
    if any(kw in description_lower for kw in religious_keywords):
        tags.append(SocialTag.RELIGIOUS)

    # Progressive keywords
    progressive_keywords = [
        "progressi", "liberal", "reforme sociale", "social reform",
        "modernisation sociale", "droits civiques", "civil rights"
    ]
    if any(kw in description_lower for kw in progressive_keywords):
        tags.append(SocialTag.PROGRESSIVE)

    # Conservative keywords
    conservative_keywords = [
        "tradition", "conservat", "valeurs familiales", "family values",
        "heritage", "patrimoine culturel"
    ]
    if any(kw in description_lower for kw in conservative_keywords):
        tags.append(SocialTag.CONSERVATIVE)

    # Nationalist keywords
    nationalist_keywords = [
        "national", "patriot", "souverain", "sovereignty", "independence",
        "protectionn"
    ]
    if any(kw in description_lower for kw in nationalist_keywords):
        tags.append(SocialTag.NATIONALIST)

    # Immigration keywords
    immigration_keywords = [
        "immigra", "migrant", "refugi", "asylum", "accueil", "integration"
    ]
    if any(kw in description_lower for kw in immigration_keywords):
        tags.append(SocialTag.IMMIGRATION)

    # Environmental keywords
    environmental_keywords = [
        "environment", "climat", "carbon", "green", "ecolog", "renouvelable",
        "renewable", "pollution", "biodiversit"
    ]
    if any(kw in description_lower for kw in environmental_keywords):
        tags.append(SocialTag.ENVIRONMENTAL)

    # Military buildup keywords
    military_keywords = [
        "military buildup", "rearmement", "nuclear weapon", "arme nucleaire",
        "course aux armements", "arms race"
    ]
    if any(kw in description_lower for kw in military_keywords):
        tags.append(SocialTag.MILITARY_BUILDUP)

    return tags
