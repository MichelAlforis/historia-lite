"""Unified world state for Historia Lite - Phase 12 Architecture"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .base_country import BaseCountry, Personality
from .tier_manager import TierManager
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


class UnifiedWorld(BaseModel):
    """
    Unified world state using BaseCountry for all countries.

    Instead of separate dicts for each tier, all countries are stored
    in a single dict. Tier information is an attribute of each country.
    """
    year: int = 2025
    seed: int = 42

    # Single unified countries dict (all tiers)
    countries: Dict[str, BaseCountry] = Field(default_factory=dict)

    # Regions and zones
    regions: Dict[str, Region] = Field(default_factory=dict)
    influence_zones: Dict[str, InfluenceZone] = Field(default_factory=dict)

    # Conflicts and events
    active_conflicts: List[Conflict] = Field(default_factory=list)
    events_history: List[Event] = Field(default_factory=list)

    # Active projects by country_id
    active_projects: Dict[str, List] = Field(default_factory=dict)

    # Global state
    oil_price: int = 80
    global_tension: int = 50

    # Tick counter for tiered processing
    tick_counter: int = 0

    # Nuclear/DEFCON system
    defcon_level: int = 5

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

    # --- Universal getters ---

    def get_country(self, country_id: str) -> Optional[BaseCountry]:
        """Get any country by ID"""
        return self.countries.get(country_id)

    def get_countries_list(self) -> List[BaseCountry]:
        """Get all countries as a list"""
        return list(self.countries.values())

    def get_all_countries_count(self) -> int:
        """Get total count of all countries"""
        return len(self.countries)

    # --- Tier-based getters ---

    def get_countries_by_tier(self, tier: int) -> List[BaseCountry]:
        """Get all countries of a specific tier"""
        return [c for c in self.countries.values() if c.tier == tier]

    def get_superpowers(self) -> List[BaseCountry]:
        """Get tier 1 superpowers"""
        return self.get_countries_by_tier(1)

    def get_major_powers(self) -> List[BaseCountry]:
        """Get tier 1 and 2 powers"""
        return [c for c in self.countries.values() if c.tier <= 2]

    def get_nuclear_powers(self) -> List[BaseCountry]:
        """Get all nuclear-armed countries"""
        return [c for c in self.countries.values() if c.is_nuclear_power()]

    def get_bloc_members(self, bloc: str) -> List[BaseCountry]:
        """Get all countries in a bloc"""
        return [c for c in self.countries.values() if bloc in c.blocs]

    # --- Region/Zone based getters ---

    def get_countries_by_region(self, region: str) -> List[BaseCountry]:
        """Get all countries in a specific region"""
        return [c for c in self.countries.values() if c.region == region]

    def get_countries_by_influence_zone(self, zone_id: str) -> List[BaseCountry]:
        """Get all countries in a specific influence zone"""
        return [c for c in self.countries.values() if c.influence_zone == zone_id]

    def get_countries_by_protector(self, protector_id: str) -> List[BaseCountry]:
        """Get all countries protected by a specific power"""
        return [c for c in self.countries.values() if c.protector == protector_id]

    # --- Alignment based getters ---

    def get_countries_by_alignment(self, alignment_label: str) -> List[BaseCountry]:
        """Get countries by alignment label"""
        return [c for c in self.countries.values()
                if c.get_alignment_label() == alignment_label]

    # --- Backwards compatibility getters (deprecated, will be removed) ---

    def get_tier4_country(self, country_id: str) -> Optional[BaseCountry]:
        """DEPRECATED: Use get_country instead"""
        country = self.countries.get(country_id)
        return country if country and country.tier == 4 else None

    def get_tier4_countries_list(self) -> List[BaseCountry]:
        """DEPRECATED: Use get_countries_by_tier(4) instead"""
        return self.get_countries_by_tier(4)

    def get_tier5_country(self, country_id: str) -> Optional[BaseCountry]:
        """DEPRECATED: Use get_country instead"""
        country = self.countries.get(country_id)
        return country if country and country.tier == 5 else None

    def get_tier5_countries_list(self) -> List[BaseCountry]:
        """DEPRECATED: Use get_countries_by_tier(5) instead"""
        return self.get_countries_by_tier(5)

    def get_tier6_country(self, country_id: str) -> Optional[BaseCountry]:
        """DEPRECATED: Use get_country instead"""
        country = self.countries.get(country_id)
        return country if country and country.tier == 6 else None

    def get_tier6_countries_list(self) -> List[BaseCountry]:
        """DEPRECATED: Use get_countries_by_tier(6) instead"""
        return self.get_countries_by_tier(6)

    # Alias for compatibility
    get_any_country = get_country

    # --- Events ---

    def add_event(self, event: Event) -> None:
        """Add an event to history"""
        self.events_history.append(event)

    def get_recent_events(self, count: int = 20) -> List[Event]:
        """Get most recent events"""
        return self.events_history[-count:]

    # --- Conflicts ---

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
        all_combatants = [self.get_country(cid) for cid in attacker_ids + defender_ids]
        if any(c and c.is_nuclear_power() for c in all_combatants):
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

    # --- Tier Processing ---

    def get_countries_to_process(self) -> List[BaseCountry]:
        """Get countries that should be processed this tick based on their frequency"""
        return [
            c for c in self.countries.values()
            if c.should_process_this_tick(self.tick_counter)
        ]

    def process_tier_changes(self) -> List[dict]:
        """Check and apply tier changes for all countries"""
        return TierManager.process_tier_changes(self.countries, self.tick_counter)

    def get_tier_stats(self) -> dict:
        """Get statistics about tier distribution"""
        return TierManager.get_tier_stats(self.countries)


def load_unified_world_from_json(data_dir: Path, seed: int = 42) -> UnifiedWorld:
    """Load unified world from countries_all.json"""
    world = UnifiedWorld(seed=seed)

    # Load unified countries file
    countries_file = data_dir / "countries_all.json"
    if countries_file.exists():
        with open(countries_file, "r", encoding="utf-8") as f:
            countries_data = json.load(f)
            for country_data in countries_data:
                tier = country_data.get("tier", 4)

                # Create BaseCountry based on tier
                if tier <= 3:
                    country = BaseCountry.from_tier1_3_data(country_data)
                elif tier == 4:
                    country = BaseCountry.from_tier4_data(country_data)
                elif tier == 5:
                    country = BaseCountry.from_tier5_data(country_data)
                else:
                    country = BaseCountry.from_tier6_data(country_data)

                world.countries[country.id] = country

        logger.info(f"Loaded {len(world.countries)} countries from countries_all.json")

        # Log tier distribution
        stats = world.get_tier_stats()
        logger.info(f"Tier distribution: {stats}")
    else:
        logger.warning(f"countries_all.json not found at {countries_file}")

    # Load influence zones
    zones_file = data_dir / "influence_zones.json"
    if zones_file.exists():
        with open(zones_file, "r", encoding="utf-8") as f:
            zones_data = json.load(f)
            for zone_data in zones_data:
                zone = InfluenceZone(**zone_data)
                world.influence_zones[zone.id] = zone
        logger.info(f"Loaded {len(world.influence_zones)} influence zones")

    # Initialize relations between major powers
    _init_major_power_relations(world)

    # Initialize alignment-based relations for smaller countries
    _init_alignment_relations(world)

    return world


def _init_major_power_relations(world: UnifiedWorld) -> None:
    """Initialize diplomatic relations between major powers (Tier 1-3)"""
    major_powers = [c for c in world.countries.values() if c.tier <= 3]

    for country in major_powers:
        for other in major_powers:
            if country.id == other.id:
                continue

            # Same bloc = positive relations
            if country.shares_bloc(other):
                base_relation = 30
            # Rivals = negative relations
            elif other.id in country.rivals:
                base_relation = -50
            # Allies = very positive
            elif other.id in country.allies:
                base_relation = 50
            else:
                base_relation = 0

            country.relations[other.id] = base_relation


def _init_alignment_relations(world: UnifiedWorld) -> None:
    """Initialize relations for Tier 4-6 countries based on alignment"""
    major_power_ids = ["USA", "CHN", "RUS", "FRA", "DEU", "GBR"]

    for country in world.countries.values():
        if country.tier <= 3:
            continue  # Already handled

        alignment = country.alignment or 0

        for power_id in major_power_ids:
            if power_id not in world.countries:
                continue

            # West-aligned powers (USA, GBR)
            if power_id in ("USA", "GBR"):
                if alignment < -30:
                    country.relations[power_id] = 30
                elif alignment > 30:
                    country.relations[power_id] = -20
                else:
                    country.relations[power_id] = 0

            # EU powers (FRA, DEU)
            elif power_id in ("FRA", "DEU"):
                if alignment < -30:
                    country.relations[power_id] = 25
                elif alignment > 30:
                    country.relations[power_id] = -10
                else:
                    country.relations[power_id] = 5

            # China
            elif power_id == "CHN":
                if alignment > 30:
                    country.relations[power_id] = 35
                elif alignment < -30:
                    country.relations[power_id] = -15
                else:
                    country.relations[power_id] = 10

            # Russia
            elif power_id == "RUS":
                if alignment > 30:
                    country.relations[power_id] = 30
                elif alignment < -30:
                    country.relations[power_id] = -25
                else:
                    country.relations[power_id] = 0
