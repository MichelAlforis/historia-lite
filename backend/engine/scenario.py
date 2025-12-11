"""Scenario system for Historia Lite - Phase 14"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ObjectiveStatus(str, Enum):
    """Status of an objective"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ObjectiveCatalogEntry(BaseModel):
    """An objective definition from the catalog"""
    name: str
    description: str
    type: str
    difficulty: str = "medium"
    points: int = 100
    check: Dict[str, Any] = Field(default_factory=dict)


class ActiveObjective(BaseModel):
    """An active objective being tracked"""
    id: str  # Catalog key like "maintain_nato_unity"
    country_id: str  # Country this objective belongs to
    name: str
    description: str
    type: str
    points: int = 100
    check: Dict[str, Any] = Field(default_factory=dict)

    # Progress tracking
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    progress: int = 0  # 0-100
    years_maintained: int = 0  # For maintain type


class ScenarioConflict(BaseModel):
    """An initial conflict in a scenario"""
    attacker: str
    defender: str
    type: str = "war"
    intensity: str = "medium"


class Scenario(BaseModel):
    """A playable scenario"""
    id: str
    name: str
    name_fr: str
    description: str
    description_fr: str = ""

    # Setup
    start_year: int = 2025
    duration: Optional[int] = None  # Years to play, None = unlimited
    difficulty: str = "normal"
    icon: str = ""

    # Tags and recommendations
    tags: List[str] = Field(default_factory=list)
    recommended_countries: List[str] = Field(default_factory=list)

    # Initial state
    initial_state: Dict[str, Any] = Field(default_factory=dict)
    modified_countries: Dict[str, Dict] = Field(default_factory=dict)
    disabled_countries: List[str] = Field(default_factory=list)

    # Conflicts
    active_conflicts: List[ScenarioConflict] = Field(default_factory=list)

    # Blocs
    blocs_override: Dict[str, List[str]] = Field(default_factory=dict)

    # Objectives by country (references to objectives_catalog)
    objectives: Dict[str, List[str]] = Field(default_factory=dict)

    # Special events
    special_events: List[Dict] = Field(default_factory=list)

    # Customization
    customizable: bool = False

    @property
    def end_year(self) -> Optional[int]:
        """Calculate end year from start_year + duration"""
        if self.duration:
            return self.start_year + self.duration
        return None


class ScenarioManager:
    """Manages scenario loading and objective tracking"""

    def __init__(self):
        self._scenarios: Dict[str, Scenario] = {}
        self._objectives_catalog: Dict[str, ObjectiveCatalogEntry] = {}
        self._difficulty_modifiers: Dict[str, Dict] = {}
        self._active_scenario: Optional[Scenario] = None
        self._data_dir: Optional[Path] = None

    def set_data_dir(self, data_dir: Path):
        """Set the data directory for loading scenarios"""
        self._data_dir = data_dir

    def load_scenarios(self, data_dir: Optional[Path] = None) -> Dict[str, Scenario]:
        """Load all scenarios from JSON file"""
        if data_dir:
            self._data_dir = data_dir

        if not self._data_dir:
            logger.warning("No data directory set for scenarios")
            return {}

        scenarios_file = self._data_dir / "scenarios.json"
        if not scenarios_file.exists():
            logger.info(f"No scenarios file found at {scenarios_file}")
            return {}

        try:
            with open(scenarios_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load objectives catalog
            self._objectives_catalog = {}
            for obj_id, obj_data in data.get("objectives_catalog", {}).items():
                self._objectives_catalog[obj_id] = ObjectiveCatalogEntry(**obj_data)

            # Load difficulty modifiers
            self._difficulty_modifiers = data.get("difficulty_modifiers", {})

            # Load scenarios
            self._scenarios = {}
            for scenario_data in data.get("scenarios", []):
                # Parse conflicts
                conflicts = []
                for conflict in scenario_data.get("active_conflicts", []):
                    conflicts.append(ScenarioConflict(**conflict))
                scenario_data["active_conflicts"] = conflicts

                scenario = Scenario(**scenario_data)
                self._scenarios[scenario.id] = scenario

            logger.info(f"Loaded {len(self._scenarios)} scenarios, "
                       f"{len(self._objectives_catalog)} objectives")
            return self._scenarios

        except Exception as e:
            logger.error(f"Error loading scenarios: {e}")
            return {}

    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get a scenario by ID"""
        return self._scenarios.get(scenario_id)

    def get_all_scenarios(self) -> List[Scenario]:
        """Get all available scenarios"""
        return list(self._scenarios.values())

    def get_objectives_catalog(self) -> Dict[str, ObjectiveCatalogEntry]:
        """Get the full objectives catalog"""
        return self._objectives_catalog

    def get_objective_info(self, objective_id: str) -> Optional[ObjectiveCatalogEntry]:
        """Get objective details from catalog"""
        return self._objectives_catalog.get(objective_id)

    def start_scenario(self, scenario_id: str, world, player_country: str = "USA") -> bool:
        """
        Start a scenario and apply it to the world.
        Returns True if successful.
        """
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            logger.error(f"Scenario {scenario_id} not found")
            return False

        self._active_scenario = scenario

        # Apply scenario to world
        world.scenario_id = scenario.id
        world.scenario_end_year = scenario.end_year
        world.player_country_id = player_country
        world.year = scenario.start_year

        # Build active objectives from catalog
        active_objectives = []
        objectives_for_player = scenario.objectives.get(player_country, [])

        for obj_id in objectives_for_player:
            catalog_entry = self._objectives_catalog.get(obj_id)
            if catalog_entry:
                active_obj = ActiveObjective(
                    id=obj_id,
                    country_id=player_country,
                    name=catalog_entry.name,
                    description=catalog_entry.description,
                    type=catalog_entry.type,
                    points=catalog_entry.points,
                    check=catalog_entry.check,
                    status=ObjectiveStatus.PENDING,
                    progress=0,
                )
                active_objectives.append(active_obj.model_dump())

        world.active_objectives = active_objectives

        # Apply initial state
        self._apply_initial_state(world, scenario)

        # Apply country modifications
        self._apply_country_modifications(world, scenario)

        logger.info(f"Started scenario: {scenario.name} as {player_country}")
        return True

    def _apply_initial_state(self, world, scenario: Scenario):
        """Apply initial state modifiers to world"""
        for key, value in scenario.initial_state.items():
            if key == "global_tension":
                world.global_tension = value
            elif key == "oil_price":
                world.oil_price = value
            elif key == "defcon_level":
                world.defcon_level = value

    def _apply_country_modifications(self, world, scenario: Scenario):
        """Apply country-specific modifications"""
        for country_id, mods in scenario.modified_countries.items():
            country = world.get_country(country_id)
            if country:
                for stat, value in mods.items():
                    if hasattr(country, stat):
                        setattr(country, stat, value)

    def check_objectives(self, world) -> List[dict]:
        """
        Check all active objectives and update their status.
        Returns list of newly completed/failed objectives.
        """
        if not self._active_scenario or not world.active_objectives:
            return []

        changes = []

        for i, obj_data in enumerate(world.active_objectives):
            obj = ActiveObjective(**obj_data)

            if obj.status in (ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED):
                continue

            old_status = obj.status
            old_progress = obj.progress

            # Check objective based on type
            self._check_objective_by_type(obj, world)

            # Mark as in progress if started
            if obj.status == ObjectiveStatus.PENDING and obj.progress > 0:
                obj.status = ObjectiveStatus.IN_PROGRESS

            # Update world storage
            world.active_objectives[i] = obj.model_dump()

            # Track changes
            if obj.status != old_status or obj.progress != old_progress:
                changes.append({
                    "objective_id": obj.id,
                    "old_status": old_status.value,
                    "new_status": obj.status.value,
                    "progress": obj.progress,
                    "name": obj.name,
                    "points": obj.points,
                })

        return changes

    def _check_objective_by_type(self, obj: ActiveObjective, world):
        """Check objective based on its type and check conditions"""
        check = obj.check
        obj_type = obj.type

        if obj_type == "survival":
            self._check_survival(obj, world)
        elif obj_type == "alliance":
            self._check_alliance(obj, world, check)
        elif obj_type == "influence":
            self._check_influence(obj, world, check)
        elif obj_type == "territorial":
            self._check_territorial(obj, world, check)
        elif obj_type == "economic":
            self._check_economic(obj, world, check)
        elif obj_type == "power":
            self._check_power(obj, world, check)
        elif obj_type == "technology":
            self._check_technology(obj, world, check)
        elif obj_type == "defense":
            self._check_defense(obj, world, check)

    def _check_survival(self, obj: ActiveObjective, world):
        """Check survival objective - maintain stability above threshold"""
        check = obj.check
        min_stability = check.get("min_stability", 30)

        player = world.get_country(obj.country_id)
        if not player:
            return

        if world.game_ended:
            obj.status = ObjectiveStatus.FAILED
        elif player.stability < min_stability:
            obj.progress = max(0, int((player.stability / min_stability) * 100))
        else:
            # Progress based on years survived
            end_year = world.scenario_end_year or 2100
            start_year = self._active_scenario.start_year if self._active_scenario else 2025
            years_passed = world.year - start_year
            total_years = end_year - start_year
            obj.progress = min(100, int((years_passed / max(1, total_years)) * 100))

            if world.year >= end_year:
                obj.status = ObjectiveStatus.COMPLETED

    def _check_alliance(self, obj: ActiveObjective, world, check: Dict):
        """Check alliance/bloc objectives"""
        bloc = check.get("bloc")
        min_members = check.get("min_members", 0)

        if bloc and min_members:
            members = world.get_bloc_members(bloc) if hasattr(world, "get_bloc_members") else []
            current_count = len(members)
            obj.progress = min(100, int((current_count / min_members) * 100))
            if current_count >= min_members:
                obj.status = ObjectiveStatus.COMPLETED

    def _check_influence(self, obj: ActiveObjective, world, check: Dict):
        """Check influence zone objectives"""
        country_id = check.get("country")
        max_zones = check.get("max_zones")
        zones_dominated = check.get("zones_dominated")

        if country_id and max_zones:
            # Prevent country from dominating too many zones
            country = world.get_country(country_id)
            if country:
                current_zones = len(getattr(country, "sphere_of_influence", []))
                if current_zones <= max_zones:
                    obj.status = ObjectiveStatus.COMPLETED
                    obj.progress = 100
                else:
                    obj.progress = max(0, int((max_zones / current_zones) * 100))

        elif zones_dominated:
            # Player needs to dominate X zones
            player = world.get_country(obj.country_id)
            if player:
                current_zones = len(getattr(player, "sphere_of_influence", []))
                obj.progress = min(100, int((current_zones / zones_dominated) * 100))
                if current_zones >= zones_dominated:
                    obj.status = ObjectiveStatus.COMPLETED

    def _check_territorial(self, obj: ActiveObjective, world, check: Dict):
        """Check territorial objectives"""
        annex_target = check.get("annex")
        country_target = check.get("country")
        status_list = check.get("status", [])

        if annex_target:
            # Check if target was annexed
            target = world.get_country(annex_target)
            if not target or getattr(target, "annexed_by", None) == obj.country_id:
                obj.status = ObjectiveStatus.COMPLETED
                obj.progress = 100

        elif country_target and status_list:
            target = world.get_country(country_target)
            if target:
                current_status = getattr(target, "political_status", "independent")
                if current_status in status_list:
                    obj.status = ObjectiveStatus.COMPLETED
                    obj.progress = 100

    def _check_economic(self, obj: ActiveObjective, world, check: Dict):
        """Check economic objectives"""
        economic_influence = check.get("economic_influence")
        oil_import_reduction = check.get("oil_import_reduction")

        if economic_influence:
            player = world.get_country(obj.country_id)
            if player:
                # Count economic partnerships/influence
                influence_count = len(getattr(player, "economic_partners", []))
                obj.progress = min(100, int((influence_count / economic_influence) * 100))
                if influence_count >= economic_influence:
                    obj.status = ObjectiveStatus.COMPLETED

    def _check_power(self, obj: ActiveObjective, world, check: Dict):
        """Check power score objectives"""
        highest = check.get("highest_power_score")

        if highest:
            player = world.get_country(obj.country_id)
            if player:
                player_score = player.get_power_score()
                max_score = max(c.get_power_score() for c in world.get_countries_list())
                obj.progress = min(100, int((player_score / max(1, max_score)) * 100))
                if player_score >= max_score:
                    obj.status = ObjectiveStatus.COMPLETED

    def _check_technology(self, obj: ActiveObjective, world, check: Dict):
        """Check technology objectives"""
        surpass = check.get("tech_score")

        if surpass and surpass.startswith("surpass_"):
            target_id = surpass.replace("surpass_", "")
            player = world.get_country(obj.country_id)
            target = world.get_country(target_id)

            if player and target:
                player_tech = getattr(player, "technology", 0) or 0
                target_tech = getattr(target, "technology", 0) or 0
                obj.progress = min(100, int((player_tech / max(1, target_tech)) * 100))
                if player_tech > target_tech:
                    obj.status = ObjectiveStatus.COMPLETED

    def _check_defense(self, obj: ActiveObjective, world, check: Dict):
        """Check defense objectives"""
        country_id = check.get("country")
        independent = check.get("independent")

        if country_id and independent:
            target = world.get_country(country_id)
            if target:
                is_independent = not getattr(target, "annexed_by", None)
                if is_independent:
                    obj.status = ObjectiveStatus.COMPLETED
                    obj.progress = 100
                else:
                    obj.status = ObjectiveStatus.FAILED
                    obj.progress = 0

    def get_scenario_score(self, world) -> int:
        """Calculate total score from completed objectives"""
        if not world.active_objectives:
            return 0

        score = 0
        for obj_data in world.active_objectives:
            obj = ActiveObjective(**obj_data)
            if obj.status == ObjectiveStatus.COMPLETED:
                score += obj.points

        return score

    def is_scenario_complete(self, world) -> bool:
        """Check if all objectives are completed"""
        if not world.active_objectives:
            return False

        for obj_data in world.active_objectives:
            obj = ActiveObjective(**obj_data)
            if obj.status != ObjectiveStatus.COMPLETED:
                return False

        return True

    def is_scenario_failed(self, world) -> bool:
        """Check if any objective has failed"""
        if not world.active_objectives:
            return False

        for obj_data in world.active_objectives:
            obj = ActiveObjective(**obj_data)
            if obj.status == ObjectiveStatus.FAILED:
                return True

        return False


# Global instance
scenario_manager = ScenarioManager()
