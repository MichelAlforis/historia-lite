"""World state for Historia Lite"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from enum import Enum
from pydantic import BaseModel, Field

from .country import Country, Tier4Country, Tier5Country, Tier6Country
from .region import InfluenceZone, Region
from .events import Event

logger = logging.getLogger(__name__)


# Month names for display
MONTH_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
MONTH_NAMES_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
]


class GameDate(BaseModel):
    """Represents a specific date in the game timeline"""
    year: int
    month: int = 1  # 1-12
    day: int = 1    # 1-31

    def __str__(self) -> str:
        """Format: 'February 15, 2025'"""
        return f"{MONTH_NAMES_EN[self.month - 1]} {self.day}, {self.year}"

    def to_french(self) -> str:
        """Format: '15 Février 2025'"""
        return f"{self.day} {MONTH_NAMES_FR[self.month - 1]} {self.year}"

    def to_display_month(self, lang: str = "fr") -> str:
        """Format: 'Février 2025' or 'February 2025'"""
        if lang == "fr":
            return f"{MONTH_NAMES_FR[self.month - 1]} {self.year}"
        return f"{MONTH_NAMES_EN[self.month - 1]} {self.year}"

    def to_ordinal(self) -> int:
        """Convert to ordinal days for comparisons (approximate)"""
        return self.year * 365 + self.month * 30 + self.day

    def to_months(self) -> int:
        """Convert to total months for easier comparisons"""
        return self.year * 12 + self.month

    def __lt__(self, other: "GameDate") -> bool:
        return self.to_ordinal() < other.to_ordinal()

    def __le__(self, other: "GameDate") -> bool:
        return self.to_ordinal() <= other.to_ordinal()

    def __gt__(self, other: "GameDate") -> bool:
        return self.to_ordinal() > other.to_ordinal()

    def __ge__(self, other: "GameDate") -> bool:
        return self.to_ordinal() >= other.to_ordinal()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GameDate):
            return False
        return self.year == other.year and self.month == other.month and self.day == other.day

    def __hash__(self) -> int:
        return hash((self.year, self.month, self.day))

    def add_months(self, months: int) -> "GameDate":
        """Return a new GameDate with months added"""
        total_months = self.year * 12 + (self.month - 1) + months
        new_year = total_months // 12
        new_month = (total_months % 12) + 1
        return GameDate(year=new_year, month=new_month, day=self.day)

    def subtract_months(self, months: int) -> "GameDate":
        """Return a new GameDate with months subtracted"""
        return self.add_months(-months)

    def months_between(self, other: "GameDate") -> int:
        """Calculate months between two dates"""
        return abs(self.to_months() - other.to_months())

    def months_since(self, other: "GameDate") -> int:
        """Calculate months since another date (can be negative)"""
        return self.to_months() - other.to_months()


class GeopoliticalEra(str, Enum):
    """Geopolitical eras that shape world dynamics - inspired by CK3/HOI4"""
    EQUILIBRIUM = "equilibrium"           # Status quo, no strong trend
    ALLIANCE_BUILDING = "alliance_building"  # Race to form alliances
    SANCTIONS_ERA = "sanctions_era"       # Economic warfare dominant
    MILITARY_BUILDUP = "military_buildup" # Generalized rearmament
    DETENTE = "detente"                   # Thaw, reconciliation
    CRISIS_MODE = "crisis_mode"           # Multiple simultaneous crises
    COLD_WAR = "cold_war"                 # East/West bipolarization
    MULTIPOLAR_SHIFT = "multipolar_shift" # Emergence of new power poles


# Era display names
ERA_NAMES_FR = {
    GeopoliticalEra.EQUILIBRIUM: "Equilibre",
    GeopoliticalEra.ALLIANCE_BUILDING: "Course aux alliances",
    GeopoliticalEra.SANCTIONS_ERA: "Ere des sanctions",
    GeopoliticalEra.MILITARY_BUILDUP: "Rearmement",
    GeopoliticalEra.DETENTE: "Detente",
    GeopoliticalEra.CRISIS_MODE: "Mode crise",
    GeopoliticalEra.COLD_WAR: "Guerre froide",
    GeopoliticalEra.MULTIPOLAR_SHIFT: "Basculement multipolaire",
}

ERA_NAMES_EN = {
    GeopoliticalEra.EQUILIBRIUM: "Equilibrium",
    GeopoliticalEra.ALLIANCE_BUILDING: "Alliance Building",
    GeopoliticalEra.SANCTIONS_ERA: "Sanctions Era",
    GeopoliticalEra.MILITARY_BUILDUP: "Military Buildup",
    GeopoliticalEra.DETENTE: "Detente",
    GeopoliticalEra.CRISIS_MODE: "Crisis Mode",
    GeopoliticalEra.COLD_WAR: "Cold War",
    GeopoliticalEra.MULTIPOLAR_SHIFT: "Multipolar Shift",
}


class WorldMood(BaseModel):
    """
    Collective emotional state of the world - influences all countries.
    This is NOT the sum of individual memories, but a distinct global state.
    """
    # Main indicators (0-100)
    global_confidence: int = 50      # Confidence in international system
    war_fatigue: int = 0             # Collective war fatigue
    economic_optimism: int = 50      # Global economic sentiment
    diplomatic_openness: int = 50    # Openness to negotiations

    # Volatility and risk
    market_volatility: int = 30      # Market instability
    nuclear_anxiety: int = 20        # Collective nuclear fear

    # Current geopolitical trend ("era")
    current_era: GeopoliticalEra = GeopoliticalEra.EQUILIBRIUM
    era_start_year: int = 2025
    era_start_month: int = 1
    era_strength: int = 50           # Strength of era (0-100)
    era_months_active: int = 0       # How long current era has been active

    # World perception of player
    player_reputation: int = 50      # How the world perceives the player

    def get_era_display(self, lang: str = "fr") -> str:
        """Get display name for current era"""
        if lang == "fr":
            return ERA_NAMES_FR.get(self.current_era, self.current_era.value)
        return ERA_NAMES_EN.get(self.current_era, self.current_era.value)

    def get_era_effects(self) -> dict:
        """Get gameplay effects of current era"""
        effects = {
            GeopoliticalEra.EQUILIBRIUM: {
                "description_fr": "Aucun modificateur particulier",
                "war_cost_modifier": 1.0,
                "diplomacy_success_modifier": 1.0,
                "sanctions_effectiveness": 1.0,
            },
            GeopoliticalEra.ALLIANCE_BUILDING: {
                "description_fr": "Les alliances se forment plus facilement",
                "alliance_formation_bonus": 0.3,
                "diplomacy_success_modifier": 1.2,
            },
            GeopoliticalEra.SANCTIONS_ERA: {
                "description_fr": "Sanctions +50% efficaces, degats militaires -30%",
                "sanctions_effectiveness": 1.5,
                "military_damage_modifier": 0.7,
            },
            GeopoliticalEra.MILITARY_BUILDUP: {
                "description_fr": "Depenses militaires reduites, tensions accrues",
                "military_cost_modifier": 0.8,
                "tension_increase_modifier": 1.3,
            },
            GeopoliticalEra.DETENTE: {
                "description_fr": "+30% succes diplomatique, guerre plus couteuse",
                "diplomacy_success_modifier": 1.3,
                "war_cost_modifier": 1.5,
            },
            GeopoliticalEra.CRISIS_MODE: {
                "description_fr": "Instabilite generalisee, tout est plus volatile",
                "stability_decay_modifier": 1.5,
                "market_volatility_bonus": 20,
            },
            GeopoliticalEra.COLD_WAR: {
                "description_fr": "Bipolarisation, proxy wars facilites",
                "bloc_cohesion_bonus": 0.2,
                "proxy_war_cost_modifier": 0.6,
            },
            GeopoliticalEra.MULTIPOLAR_SHIFT: {
                "description_fr": "Nouveaux acteurs emergent, alliances fluides",
                "new_alliance_bonus": 0.4,
                "bloc_cohesion_penalty": 0.2,
            },
        }
        return effects.get(self.current_era, effects[GeopoliticalEra.EQUILIBRIUM])

    def to_dict(self) -> dict:
        """Serialize for API/frontend"""
        return {
            "global_confidence": self.global_confidence,
            "war_fatigue": self.war_fatigue,
            "economic_optimism": self.economic_optimism,
            "diplomatic_openness": self.diplomatic_openness,
            "market_volatility": self.market_volatility,
            "nuclear_anxiety": self.nuclear_anxiety,
            "current_era": self.current_era.value,
            "era_display_fr": self.get_era_display("fr"),
            "era_display_en": self.get_era_display("en"),
            "era_strength": self.era_strength,
            "era_months_active": self.era_months_active,
            "era_effects": self.get_era_effects(),
            "player_reputation": self.player_reputation,
        }


class Conflict(BaseModel):
    """Active conflict between countries"""
    id: str
    type: str = "war"
    attackers: List[str] = Field(default_factory=list)
    defenders: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    intensity: int = Field(default=5, ge=1, le=10)
    duration: int = 0
    nuclear_risk: int = Field(default=0, ge=0, le=100)


class World(BaseModel):
    """The complete game world state"""
    # Timeline - now with month granularity
    year: int = 2025
    month: int = 1      # 1-12
    day: int = 1        # 1-31 (current day in simulation)
    start_year: int = 2025
    start_month: int = 1

    seed: int = 42

    countries: Dict[str, Country] = Field(default_factory=dict)
    tier4_countries: Dict[str, Tier4Country] = Field(default_factory=dict)
    tier5_countries: Dict[str, Tier5Country] = Field(default_factory=dict)
    tier6_countries: Dict[str, Tier6Country] = Field(default_factory=dict)
    regions: Dict[str, Region] = Field(default_factory=dict)
    influence_zones: Dict[str, InfluenceZone] = Field(default_factory=dict)

    active_conflicts: List[Conflict] = Field(default_factory=list)
    events_history: List[Event] = Field(default_factory=list)

    # Active projects by country_id
    active_projects: Dict[str, List] = Field(default_factory=dict)

    oil_price: int = 80
    global_tension: int = 50

    # Tick counter for tiered processing (now monthly)
    tick_counter: int = 0
    # Tier 4: process when tick_counter % 6 == 0 (every 6 months)
    # Tier 5: process when tick_counter % 12 == 0 (every 12 months)
    # Tier 6: process when tick_counter % 24 == 0 (every 24 months)

    # Nuclear/DEFCON system
    defcon_level: int = 5  # 5=peace, 1=imminent war, 0=nuclear war

    # World Mood - collective emotional state (Phase 2 Timeline)
    mood: WorldMood = Field(default_factory=WorldMood)

    # Game state
    game_ended: bool = False
    game_end_reason: Optional[str] = None
    game_end_message: str = ""
    game_end_message_fr: str = ""
    final_score: int = 0

    # Scenario tracking
    scenario_id: Optional[str] = None
    scenario_end_year: Optional[int] = None
    active_objectives: List[dict] = Field(default_factory=list)

    # Player tracking
    player_country_id: Optional[str] = None

    @property
    def current_date(self) -> GameDate:
        """Get current date as GameDate object"""
        return GameDate(year=self.year, month=self.month, day=self.day)

    @property
    def date_display(self) -> str:
        """Format for UI display: 'Février 2025'"""
        return f"{MONTH_NAMES_FR[self.month - 1]} {self.year}"

    @property
    def date_display_en(self) -> str:
        """Format for UI display: 'February 2025'"""
        return f"{MONTH_NAMES_EN[self.month - 1]} {self.year}"

    @property
    def total_months_elapsed(self) -> int:
        """Total months since game start"""
        start_months = self.start_year * 12 + self.start_month
        current_months = self.year * 12 + self.month
        return current_months - start_months

    def advance_month(self) -> None:
        """Advance the calendar by one month"""
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.day = 1  # Reset to 1st of new month
        self.tick_counter += 1

    def get_country(self, country_id: str) -> Optional[Country]:
        """Get a country by ID"""
        return self.countries.get(country_id)

    def get_countries_list(self) -> List[Country]:
        """Get all countries as a list"""
        return list(self.countries.values())

    def get_superpowers(self) -> List[Country]:
        """Get tier 1 superpowers"""
        return [c for c in self.countries.values() if c.tier == 1]

    def get_major_powers(self) -> List[Country]:
        """Get tier 1 and 2 powers"""
        return [c for c in self.countries.values() if c.tier <= 2]

    def get_nuclear_powers(self) -> List[Country]:
        """Get all nuclear-armed countries"""
        return [c for c in self.countries.values() if c.is_nuclear_power()]

    def get_bloc_members(self, bloc: str) -> List[Country]:
        """Get all countries in a bloc"""
        return [c for c in self.countries.values() if bloc in c.blocs]

    def get_tier4_country(self, country_id: str) -> Optional[Tier4Country]:
        """Get a Tier 4 country by ID"""
        return self.tier4_countries.get(country_id)

    def get_tier4_countries_list(self) -> List[Tier4Country]:
        """Get all Tier 4 countries as a list"""
        return list(self.tier4_countries.values())

    def get_tier4_by_region(self, region: str) -> List[Tier4Country]:
        """Get all Tier 4 countries in a specific region"""
        return [c for c in self.tier4_countries.values() if c.region == region]

    def get_tier4_by_alignment(self, alignment_label: str) -> List[Tier4Country]:
        """Get Tier 4 countries by alignment label"""
        return [c for c in self.tier4_countries.values()
                if c.get_alignment_label() == alignment_label]

    # Tier 5 getters
    def get_tier5_country(self, country_id: str) -> Optional[Tier5Country]:
        """Get a Tier 5 country by ID"""
        return self.tier5_countries.get(country_id)

    def get_tier5_countries_list(self) -> List[Tier5Country]:
        """Get all Tier 5 countries as a list"""
        return list(self.tier5_countries.values())

    def get_tier5_by_region(self, region: str) -> List[Tier5Country]:
        """Get all Tier 5 countries in a specific region"""
        return [c for c in self.tier5_countries.values() if c.region == region]

    def get_tier5_by_alignment(self, alignment_label: str) -> List[Tier5Country]:
        """Get Tier 5 countries by alignment label"""
        return [c for c in self.tier5_countries.values()
                if c.get_alignment_label() == alignment_label]

    def get_tier5_by_protector(self, protector_id: str) -> List[Tier5Country]:
        """Get Tier 5 countries protected by a specific power"""
        return [c for c in self.tier5_countries.values()
                if c.protector == protector_id]

    # Tier 6 getters
    def get_tier6_country(self, country_id: str) -> Optional[Tier6Country]:
        """Get a Tier 6 country by ID"""
        return self.tier6_countries.get(country_id)

    def get_tier6_countries_list(self) -> List[Tier6Country]:
        """Get all Tier 6 countries as a list"""
        return list(self.tier6_countries.values())

    def get_tier6_by_region(self, region: str) -> List[Tier6Country]:
        """Get all Tier 6 countries in a specific region"""
        return [c for c in self.tier6_countries.values() if c.region == region]

    def get_tier6_by_protector(self, protector_id: str) -> List[Tier6Country]:
        """Get Tier 6 countries protected by a specific power"""
        return [c for c in self.tier6_countries.values()
                if c.protector == protector_id]

    # Universal getters
    def get_any_country(self, country_id: str):
        """Get any country by ID (searches all tiers)"""
        if country_id in self.countries:
            return self.countries[country_id]
        if country_id in self.tier4_countries:
            return self.tier4_countries[country_id]
        if country_id in self.tier5_countries:
            return self.tier5_countries[country_id]
        if country_id in self.tier6_countries:
            return self.tier6_countries[country_id]
        return None

    def get_countries_by_influence_zone(self, zone_id: str) -> List:
        """Get all countries in a specific influence zone (Tier 4-6)"""
        result = []
        for c in self.tier4_countries.values():
            if c.influence_zone == zone_id:
                result.append(c)
        for c in self.tier5_countries.values():
            if c.influence_zone == zone_id:
                result.append(c)
        for c in self.tier6_countries.values():
            if c.influence_zone == zone_id:
                result.append(c)
        return result

    def get_all_countries_count(self) -> int:
        """Get total count of all countries (Tier 1-6)"""
        return (len(self.countries) + len(self.tier4_countries) +
                len(self.tier5_countries) + len(self.tier6_countries))

    def add_event(self, event: Event) -> None:
        """Add an event to history"""
        self.events_history.append(event)

    def get_recent_events(self, count: int = 20) -> List[Event]:
        """Get most recent events"""
        return self.events_history[-count:]

    def start_conflict(
        self,
        attacker_ids: List[str],
        defender_ids: List[str],
        conflict_type: str = "war",
        region: Optional[str] = None,
    ) -> Conflict:
        """Start a new conflict"""
        conflict = Conflict(
            id=f"conflict_{self.year}_{attacker_ids[0]}_{defender_ids[0]}",
            type=conflict_type,
            attackers=attacker_ids,
            defenders=defender_ids,
            region=region,
        )

        for attacker_id in attacker_ids:
            attacker = self.get_country(attacker_id)
            if attacker:
                for defender_id in defender_ids:
                    if defender_id not in attacker.at_war:
                        attacker.at_war.append(defender_id)

        for defender_id in defender_ids:
            defender = self.get_country(defender_id)
            if defender:
                for attacker_id in attacker_ids:
                    if attacker_id not in defender.at_war:
                        defender.at_war.append(attacker_id)

        # Calculate nuclear risk
        attackers = [self.get_country(cid) for cid in attacker_ids]
        defenders = [self.get_country(cid) for cid in defender_ids]
        if any(c and c.is_nuclear_power() for c in attackers + defenders):
            conflict.nuclear_risk = 20

        self.active_conflicts.append(conflict)
        logger.info(f"Conflict started: {conflict.id}")
        return conflict

    def end_conflict(self, conflict_id: str) -> None:
        """End a conflict"""
        conflict = next(
            (c for c in self.active_conflicts if c.id == conflict_id), None
        )
        if not conflict:
            return

        for attacker_id in conflict.attackers:
            attacker = self.get_country(attacker_id)
            if attacker:
                for defender_id in conflict.defenders:
                    if defender_id in attacker.at_war:
                        attacker.at_war.remove(defender_id)

        for defender_id in conflict.defenders:
            defender = self.get_country(defender_id)
            if defender:
                for attacker_id in conflict.attackers:
                    if attacker_id in defender.at_war:
                        defender.at_war.remove(attacker_id)

        self.active_conflicts.remove(conflict)
        logger.info(f"Conflict ended: {conflict_id}")


def load_world_from_json(data_dir: Path, seed: int = 42) -> World:
    """Load world from JSON data files"""
    world = World(seed=seed)

    # Load countries (Tier 1-3)
    countries_file = data_dir / "countries.json"
    if countries_file.exists():
        with open(countries_file, "r", encoding="utf-8") as f:
            countries_data = json.load(f)
            for country_data in countries_data:
                country = Country(**country_data)
                world.countries[country.id] = country
        logger.info(f"Loaded {len(world.countries)} countries (Tier 1-3)")

    # Load Tier 4 countries
    tier4_file = data_dir / "countries_tier4.json"
    if tier4_file.exists():
        with open(tier4_file, "r", encoding="utf-8") as f:
            tier4_data = json.load(f)
            countries_list = tier4_data.get("countries", [])
            for country_data in countries_list:
                country = Tier4Country(**country_data)
                world.tier4_countries[country.id] = country
        logger.info(f"Loaded {len(world.tier4_countries)} Tier 4 countries")

    # Load Tier 5 countries
    tier5_file = data_dir / "countries_tier5.json"
    if tier5_file.exists():
        with open(tier5_file, "r", encoding="utf-8") as f:
            tier5_data = json.load(f)
            countries_list = tier5_data.get("countries", [])
            for country_data in countries_list:
                country = Tier5Country(**country_data)
                world.tier5_countries[country.id] = country
        logger.info(f"Loaded {len(world.tier5_countries)} Tier 5 countries")

    # Load Tier 6 countries
    tier6_file = data_dir / "countries_tier6.json"
    if tier6_file.exists():
        with open(tier6_file, "r", encoding="utf-8") as f:
            tier6_data = json.load(f)
            countries_list = tier6_data.get("countries", [])
            for country_data in countries_list:
                country = Tier6Country(**country_data)
                world.tier6_countries[country.id] = country
        logger.info(f"Loaded {len(world.tier6_countries)} Tier 6 countries")

    # Load influence zones
    zones_file = data_dir / "influence_zones.json"
    if zones_file.exists():
        with open(zones_file, "r", encoding="utf-8") as f:
            zones_data = json.load(f)
            for zone_data in zones_data:
                zone = InfluenceZone(**zone_data)
                world.influence_zones[zone.id] = zone
        logger.info(f"Loaded {len(world.influence_zones)} influence zones")

    # Initialize relations between countries
    _init_relations(world)

    # Initialize Tier 4 relations with major powers
    _init_tier4_relations(world)

    return world


def _init_relations(world: World) -> None:
    """Initialize diplomatic relations based on blocs and rivalries"""
    for country in world.countries.values():
        for other in world.countries.values():
            if country.id == other.id:
                continue

            # Same bloc = positive relations
            if country.shares_bloc(other):
                base_relation = 30
            # Rivals = negative relations
            elif other.id in country.rivals:
                base_relation = -50
            else:
                base_relation = 0

            country.relations[other.id] = base_relation


def _init_tier4_relations(world: World) -> None:
    """Initialize Tier 4 countries relations with major powers"""
    major_powers = ["USA", "CHN", "RUS", "FRA", "DEU", "GBR"]

    for country in world.tier4_countries.values():
        # Set relations based on alignment
        for power_id in major_powers:
            if power_id not in world.countries:
                continue

            # West-aligned powers
            if power_id in ("USA", "GBR"):
                # Pro-West countries have good relations with USA/UK
                if country.alignment < -30:
                    country.relations[power_id] = 30
                elif country.alignment > 30:
                    country.relations[power_id] = -20
                else:
                    country.relations[power_id] = 0

            # EU powers
            elif power_id in ("FRA", "DEU"):
                if country.alignment < -30:
                    country.relations[power_id] = 25
                elif country.alignment > 30:
                    country.relations[power_id] = -10
                else:
                    country.relations[power_id] = 5

            # China
            elif power_id == "CHN":
                if country.alignment > 30:
                    country.relations[power_id] = 35
                elif country.alignment < -30:
                    country.relations[power_id] = -15
                else:
                    country.relations[power_id] = 10  # China invests everywhere

            # Russia
            elif power_id == "RUS":
                if country.alignment > 30:
                    country.relations[power_id] = 30
                elif country.alignment < -30:
                    country.relations[power_id] = -25
                else:
                    country.relations[power_id] = 0
