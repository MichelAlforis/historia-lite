"""API response schemas for Historia Lite"""
from typing import Dict, List, Optional
from pydantic import BaseModel

from engine.country import Country, Personality, Tier4Country, Tier5Country, Tier6Country
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


class Tier5CountryResponse(BaseModel):
    """Response for Tier 5 countries (small nations)"""
    id: str
    name: str
    name_fr: str
    flag: str
    tier: int
    region: str

    # Minimal stats
    economy: int
    stability: int
    population: int
    alignment: int
    alignment_label: str

    # Protection
    protector: Optional[str]
    influence_zone: Optional[str]

    # Status
    in_crisis: bool
    crisis_type: Optional[str]

    # Neighbors
    neighbors: List[str]

    power_score: float

    @classmethod
    def from_tier5_country(cls, country: Tier5Country) -> "Tier5CountryResponse":
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
            alignment=country.alignment,
            alignment_label=country.get_alignment_label(),
            protector=country.protector,
            influence_zone=country.influence_zone,
            in_crisis=country.in_crisis,
            crisis_type=country.crisis_type,
            neighbors=country.neighbors,
            power_score=round(country.get_power_score(), 1),
        )


class Tier5SummaryResponse(BaseModel):
    """Summary statistics for Tier 5 countries"""
    total: int
    by_region: Dict[str, int]
    by_alignment: Dict[str, int]
    by_protector: Dict[str, int]
    in_crisis: int
    pro_west: int
    pro_east: int
    neutral: int


class Tier6CountryResponse(BaseModel):
    """Response for Tier 6 countries (micro-nations)"""
    id: str
    name: str
    name_fr: str
    flag: str
    tier: int
    region: str

    # Ultra-minimal stats
    economy: int
    stability: int
    population: int

    # Protection (usually required for Tier 6)
    protector: Optional[str]
    influence_zone: Optional[str]

    # Special status
    is_territory: bool
    special_status: Optional[str]

    power_score: float

    @classmethod
    def from_tier6_country(cls, country: Tier6Country) -> "Tier6CountryResponse":
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
            protector=country.protector,
            influence_zone=country.influence_zone,
            is_territory=country.is_territory,
            special_status=country.special_status,
            power_score=round(country.get_power_score(), 1),
        )


class Tier6SummaryResponse(BaseModel):
    """Summary statistics for Tier 6 countries"""
    total: int
    by_region: Dict[str, int]
    by_protector: Dict[str, int]
    by_special_status: Dict[str, int]
    territories: int
    sovereign: int


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
    month: int = 1  # NEW: month field (1-12)
    date_display: str = ""  # NEW: "Janvier 2025" format
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

    # Tier counts and crisis summary
    tier4_count: int = 0
    tier4_in_crisis: int = 0
    tier5_count: int = 0
    tier5_in_crisis: int = 0
    tier6_count: int = 0

    # Game state
    defcon_level: int = 5
    game_ended: bool = False
    game_end_reason: Optional[str] = None
    game_end_message: str = ""
    game_end_message_fr: str = ""
    final_score: int = 0

    # Timeline stats (NEW)
    unread_events: int = 0
    timeline_total: int = 0


class TickResponse(BaseModel):
    year: int
    events: List[EventResponse]
    summary: str
    summary_fr: str

    # Game end state (if game ended this tick)
    game_ended: bool = False
    game_end_reason: Optional[str] = None
    game_end_message: str = ""
    game_end_message_fr: str = ""
    is_victory: bool = False
    final_score: int = 0
    defcon_level: int = 5
