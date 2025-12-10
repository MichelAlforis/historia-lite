"""Event system for Historia Lite"""
import logging
import random
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventEffect(BaseModel):
    """Effect of an event on a country or world"""
    stat: str
    delta: int
    target: str = "self"


class Event(BaseModel):
    """A game event that occurred"""
    id: str
    year: int
    type: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    country_id: Optional[str] = None
    target_id: Optional[str] = None
    effects: List[EventEffect] = Field(default_factory=list)


class EventTemplate(BaseModel):
    """Template for generating events"""
    id: str
    type: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    probability: float = 0.05
    conditions: Dict[str, Any] = Field(default_factory=dict)
    effects: List[EventEffect] = Field(default_factory=list)

    def check_conditions(self, country: Any) -> bool:
        """Check if event conditions are met"""
        for stat, constraint in self.conditions.items():
            value = getattr(country, stat, None)
            if value is None:
                continue

            if isinstance(constraint, dict):
                if "min" in constraint and value < constraint["min"]:
                    return False
                if "max" in constraint and value > constraint["max"]:
                    return False
            elif isinstance(constraint, (int, float)):
                if value < constraint:
                    return False

        return True


class EventPool:
    """Pool of event templates for the simulation"""

    def __init__(self):
        self.templates: List[EventTemplate] = []
        self._load_default_events()

    def _load_default_events(self) -> None:
        """Load default event templates"""
        self.templates = [
            # Crises
            EventTemplate(
                id="economic_crisis",
                type="crisis",
                title="Economic Crisis",
                title_fr="Crise economique",
                description="{country} faces a severe economic crisis",
                description_fr="{country} fait face a une grave crise economique",
                probability=0.03,
                conditions={"economy": {"max": 60}},
                effects=[
                    EventEffect(stat="economy", delta=-15),
                    EventEffect(stat="stability", delta=-10),
                ],
            ),
            EventTemplate(
                id="pandemic",
                type="crisis",
                title="Pandemic Outbreak",
                title_fr="Epidemie",
                description="A pandemic spreads in {country}",
                description_fr="Une epidemie se propage en {country}",
                probability=0.01,
                conditions={},
                effects=[
                    EventEffect(stat="population", delta=-5),
                    EventEffect(stat="economy", delta=-10),
                ],
            ),
            EventTemplate(
                id="cyberattack",
                type="crisis",
                title="Major Cyberattack",
                title_fr="Cyberattaque majeure",
                description="{country} suffers a devastating cyberattack",
                description_fr="{country} subit une cyberattaque devastatrice",
                probability=0.04,
                conditions={"technology": {"min": 40}},
                effects=[
                    EventEffect(stat="technology", delta=-10),
                    EventEffect(stat="military", delta=-5),
                ],
            ),
            EventTemplate(
                id="social_unrest",
                type="crisis",
                title="Mass Social Movement",
                title_fr="Mouvement social massif",
                description="Mass protests erupt in {country}",
                description_fr="Des manifestations massives eclatent en {country}",
                probability=0.05,
                conditions={"stability": {"max": 50}},
                effects=[
                    EventEffect(stat="stability", delta=-15),
                ],
            ),
            # Positive events
            EventTemplate(
                id="tech_boom",
                type="positive",
                title="Technological Boom",
                title_fr="Boom technologique",
                description="{country} experiences a tech boom",
                description_fr="{country} connait un boom technologique",
                probability=0.04,
                conditions={"technology": {"min": 60}},
                effects=[
                    EventEffect(stat="technology", delta=10),
                    EventEffect(stat="economy", delta=5),
                ],
            ),
            EventTemplate(
                id="resource_discovery",
                type="positive",
                title="Resource Discovery",
                title_fr="Decouverte de ressources",
                description="New resources discovered in {country}",
                description_fr="Nouvelles ressources decouvertes en {country}",
                probability=0.02,
                conditions={},
                effects=[
                    EventEffect(stat="resources", delta=15),
                    EventEffect(stat="economy", delta=5),
                ],
            ),
            EventTemplate(
                id="golden_age",
                type="positive",
                title="Golden Age",
                title_fr="Age d'or",
                description="{country} enters a golden age",
                description_fr="{country} entre dans un age d'or",
                probability=0.02,
                conditions={"stability": {"min": 70}, "economy": {"min": 60}},
                effects=[
                    EventEffect(stat="soft_power", delta=15),
                    EventEffect(stat="economy", delta=10),
                ],
            ),
            # Geopolitical
            EventTemplate(
                id="diplomatic_summit",
                type="diplomacy",
                title="Diplomatic Summit",
                title_fr="Sommet diplomatique",
                description="{country} hosts a major diplomatic summit",
                description_fr="{country} organise un sommet diplomatique majeur",
                probability=0.03,
                conditions={"soft_power": {"min": 50}},
                effects=[
                    EventEffect(stat="soft_power", delta=10),
                ],
            ),
            EventTemplate(
                id="arms_race",
                type="military",
                title="Arms Race",
                title_fr="Course aux armements",
                description="{country} accelerates military buildup",
                description_fr="{country} accelere son renforcement militaire",
                probability=0.04,
                conditions={"military": {"min": 50}},
                effects=[
                    EventEffect(stat="military", delta=10),
                    EventEffect(stat="economy", delta=-5),
                ],
            ),
            EventTemplate(
                id="nuclear_test",
                type="military",
                title="Nuclear Test",
                title_fr="Essai nucleaire",
                description="{country} conducts nuclear tests",
                description_fr="{country} procede a des essais nucleaires",
                probability=0.02,
                conditions={"nuclear": {"min": 20}},
                effects=[
                    EventEffect(stat="nuclear", delta=10),
                    EventEffect(stat="soft_power", delta=-10),
                ],
            ),
        ]

    def get_random_events(
        self, countries: List[Any], year: int, seed: Optional[int] = None
    ) -> List[Event]:
        """Generate random events for this tick"""
        if seed is not None:
            random.seed(seed + year)

        events = []
        for country in countries:
            for template in self.templates:
                if not template.check_conditions(country):
                    continue

                if random.random() < template.probability:
                    event = Event(
                        id=f"{template.id}_{year}_{country.id}",
                        year=year,
                        type=template.type,
                        title=template.title,
                        title_fr=template.title_fr,
                        description=template.description.format(country=country.name_fr),
                        description_fr=template.description_fr.format(
                            country=country.name_fr
                        ),
                        country_id=country.id,
                        effects=template.effects,
                    )
                    events.append(event)
                    logger.info(f"Event triggered: {event.title_fr} for {country.id}")

        return events
