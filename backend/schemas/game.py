"""API response schemas for Historia Lite"""
from typing import Dict, List, Optional
from pydantic import BaseModel

from engine.country import Country, Personality, Tier4Country
from engine.region import InfluenceZone
from engine.events import Event


class PersonalityResponse(BaseModel):
    aggression: int
    expansionism: int
    diplomacy: int
    risk_tolerance: int


class CountryResponse(BaseModel):
    id: str
    name: str
    name_fr: str
    tier: int

    population: int
    economy: int
    military: int
    nuclear: int
    technology: int
    stability: int
    soft_power: int
    resources: int

    personality: PersonalityResponse
    regime: str
    blocs: List[str]
    relations: Dict[str, int]
    sanctions_on: List[str]
    at_war: List[str]
    allies: List[str]
    rivals: List[str]
    sphere_of_influence: List[str]
    under_influence_of: Dict[str, int]
    is_player: bool
    power_score: float

    @classmethod
    def from_country(cls, country: Country) -> "CountryResponse":
        return cls(
            id=country.id,
            name=country.name,
            name_fr=country.name_fr,
            tier=country.tier,
            population=country.population,
            economy=country.economy,
            military=country.military,
            nuclear=country.nuclear,
            technology=country.technology,
            stability=country.stability,
            soft_power=country.soft_power,
            resources=country.resources,
            personality=PersonalityResponse(
                aggression=country.personality.aggression,
                expansionism=country.personality.expansionism,
                diplomacy=country.personality.diplomacy,
                risk_tolerance=country.personality.risk_tolerance,
            ),
            regime=country.regime,
            blocs=country.blocs,
            relations=country.relations,
            sanctions_on=country.sanctions_on,
            at_war=country.at_war,
            allies=country.allies,
            rivals=country.rivals,
            sphere_of_influence=country.sphere_of_influence,
            under_influence_of=country.under_influence_of,
            is_player=country.is_player,
            power_score=round(country.get_power_score(), 1),
        )


class Tier4CountryResponse(BaseModel):
    """Simplified response for Tier 4 countries"""
    id: str
    name: str
    name_fr: str
    flag: str
    tier: int
    region: str

    # Simplified stats
    economy: int
    stability: int
    population: int
    military: int

    # Alignment
    alignment: int
    alignment_target: str
    alignment_label: str

    # Resources
    strategic_resource: Optional[str]

    # Relations with major powers
    relations: Dict[str, int]

    # Status
    in_crisis: bool
    crisis_type: Optional[str]
    under_influence_of: Optional[str]

    power_score: float

    @classmethod
    def from_tier4_country(cls, country: Tier4Country) -> "Tier4CountryResponse":
        return cls(
            id=country.id,
            name=country.name,
            name_fr=country.name_fr,
            flag=country.flag,
            tier=country.tier,
            region=country.region,
            economy=country.economy,
            stability=country.stability,
            population=country.population,
            military=country.military,
            alignment=country.alignment,
            alignment_target=country.alignment_target,
            alignment_label=country.get_alignment_label(),
            strategic_resource=country.strategic_resource,
            relations=country.relations,
            in_crisis=country.in_crisis,
            crisis_type=country.crisis_type,
            under_influence_of=country.under_influence_of,
            power_score=round(country.get_power_score(), 1),
        )


class Tier4SummaryResponse(BaseModel):
    """Summary statistics for Tier 4 countries"""
    total: int
    by_region: Dict[str, int]
    by_alignment: Dict[str, int]
    in_crisis: int
    pro_west: int
    pro_east: int
    neutral: int


class InfluenceZoneResponse(BaseModel):
    id: str
    name: str
    name_fr: str
    dominant_power: Optional[str]
    contested_by: List[str]
    countries_in_zone: List[str]
    influence_type: str
    strength: int
    influence_levels: Dict[str, int]

    @classmethod
    def from_zone(cls, zone: InfluenceZone) -> "InfluenceZoneResponse":
        return cls(
            id=zone.id,
            name=zone.name,
            name_fr=zone.name_fr,
            dominant_power=zone.get_dominant_power(),
            contested_by=zone.contested_by,
            countries_in_zone=zone.countries_in_zone,
            influence_type=zone.influence_type,
            strength=zone.strength,
            influence_levels=zone.influence_levels,
        )


class EventResponse(BaseModel):
    id: str
    year: int
    type: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    country_id: Optional[str]
    target_id: Optional[str]

    @classmethod
    def from_event(cls, event: Event) -> "EventResponse":
        return cls(
            id=event.id,
            year=event.year,
            type=event.type,
            title=event.title,
            title_fr=event.title_fr,
            description=event.description,
            description_fr=event.description_fr,
            country_id=event.country_id,
            target_id=event.target_id,
        )


class ConflictResponse(BaseModel):
    id: str
    type: str
    attackers: List[str]
    defenders: List[str]
    region: Optional[str]
    intensity: int
    duration: int
    nuclear_risk: int


class WorldStateResponse(BaseModel):
    year: int
    seed: int
    oil_price: int
    global_tension: int

    countries: List[CountryResponse]
    influence_zones: List[InfluenceZoneResponse]
    active_conflicts: List[ConflictResponse]
    recent_events: List[EventResponse]

    # Summary stats
    total_countries: int
    nuclear_powers: int
    active_wars: int

    # Tier 4 summary
    tier4_count: int = 0
    tier4_in_crisis: int = 0


class TickResponse(BaseModel):
    year: int
    events: List[EventResponse]
    summary: str
    summary_fr: str
