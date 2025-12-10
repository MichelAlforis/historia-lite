"""World state for Historia Lite"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .country import Country, Tier4Country
from .region import InfluenceZone, Region
from .events import Event

logger = logging.getLogger(__name__)


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
    year: int = 2025
    seed: int = 42

    countries: Dict[str, Country] = Field(default_factory=dict)
    tier4_countries: Dict[str, Tier4Country] = Field(default_factory=dict)
    regions: Dict[str, Region] = Field(default_factory=dict)
    influence_zones: Dict[str, InfluenceZone] = Field(default_factory=dict)

    active_conflicts: List[Conflict] = Field(default_factory=list)
    events_history: List[Event] = Field(default_factory=list)

    # Active projects by country_id
    active_projects: Dict[str, List] = Field(default_factory=dict)

    oil_price: int = 80
    global_tension: int = 50

    # Tick counter for Tier 4 processing (every 3 ticks)
    tier4_tick_counter: int = 0

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

    def get_all_countries_count(self) -> int:
        """Get total count of all countries (Tier 1-4)"""
        return len(self.countries) + len(self.tier4_countries)

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
