"""
Historia Lite - Scenarios & Objectives API Routes (Phase 14)
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from pathlib import Path

from engine.scenario import scenario_manager
from api.game_state import get_world, get_data_dir, is_unified_mode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
SCENARIOS_FILE = DATA_DIR / "scenarios.json"


def load_scenarios() -> dict:
    """Load scenarios from JSON file"""
    if SCENARIOS_FILE.exists():
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenarios": [], "objectives_catalog": {}, "difficulty_modifiers": {}}


def _ensure_scenarios_loaded():
    """Ensure scenarios are loaded into scenario_manager"""
    if not scenario_manager._scenarios:
        scenario_manager.load_scenarios(get_data_dir())


# Pydantic models
class ScenarioSummary(BaseModel):
    id: str
    name: str
    name_fr: str
    description: str
    start_year: int
    difficulty: str
    duration: Optional[int] = None
    icon: str
    tags: List[str]


class ObjectiveSummary(BaseModel):
    id: str
    name: str
    description: str
    type: str
    difficulty: str
    points: int


class ScenarioDetail(ScenarioSummary):
    initial_state: Dict[str, Any]
    objectives: Dict[str, List[str]]
    active_conflicts: List[Dict[str, Any]] = []
    modified_countries: Dict[str, Any] = {}
    recommended_countries: List[str] = []
    customizable: bool = False


class StartScenarioRequest(BaseModel):
    scenario_id: str
    player_country: Optional[str] = None
    difficulty_override: Optional[str] = None


class ObjectiveProgress(BaseModel):
    objective_id: str
    name: str
    description: str
    progress: float  # 0-100
    completed: bool
    points: int


# Routes

@router.get("/")
async def list_scenarios():
    """List all available scenarios"""
    data = load_scenarios()
    scenarios = [
        ScenarioSummary(
            id=s["id"],
            name=s["name"],
            name_fr=s["name_fr"],
            description=s["description"],
            start_year=s["start_year"],
            difficulty=s["difficulty"],
            duration=s.get("duration"),
            icon=s["icon"],
            tags=s["tags"]
        )
        for s in data["scenarios"]
    ]
    return {"scenarios": scenarios, "total": len(scenarios)}


@router.get("/{scenario_id}", response_model=ScenarioDetail)
async def get_scenario(scenario_id: str):
    """Get detailed scenario information"""
    data = load_scenarios()

    for scenario in data["scenarios"]:
        if scenario["id"] == scenario_id:
            return ScenarioDetail(
                id=scenario["id"],
                name=scenario["name"],
                name_fr=scenario["name_fr"],
                description=scenario["description"],
                start_year=scenario["start_year"],
                difficulty=scenario["difficulty"],
                duration=scenario.get("duration"),
                icon=scenario["icon"],
                tags=scenario["tags"],
                initial_state=scenario.get("initial_state", {}),
                objectives=scenario.get("objectives", {}),
                active_conflicts=scenario.get("active_conflicts", []),
                modified_countries=scenario.get("modified_countries", {}),
                recommended_countries=scenario.get("recommended_countries", []),
                customizable=scenario.get("customizable", False)
            )

    raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")


@router.get("/objectives/catalog", response_model=List[ObjectiveSummary])
async def list_objectives():
    """List all objectives from catalog"""
    data = load_scenarios()
    catalog = data.get("objectives_catalog", {})

    return [
        ObjectiveSummary(
            id=obj_id,
            name=obj["name"],
            description=obj["description"],
            type=obj["type"],
            difficulty=obj["difficulty"],
            points=obj["points"]
        )
        for obj_id, obj in catalog.items()
    ]


@router.get("/objectives/{objective_id}")
async def get_objective(objective_id: str):
    """Get detailed objective information"""
    data = load_scenarios()
    catalog = data.get("objectives_catalog", {})

    if objective_id not in catalog:
        raise HTTPException(status_code=404, detail=f"Objective {objective_id} not found")

    obj = catalog[objective_id]
    return {
        "id": objective_id,
        **obj
    }


@router.get("/{scenario_id}/objectives/{country_id}", response_model=List[ObjectiveProgress])
async def get_country_objectives(scenario_id: str, country_id: str):
    """Get objectives and progress for a specific country in a scenario"""
    data = load_scenarios()

    # Find scenario
    scenario = None
    for s in data["scenarios"]:
        if s["id"] == scenario_id:
            scenario = s
            break

    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    # Get country objectives
    country_objectives = scenario.get("objectives", {}).get(country_id, [])
    catalog = data.get("objectives_catalog", {})

    results = []
    for obj_id in country_objectives:
        if obj_id in catalog:
            obj = catalog[obj_id]
            # TODO: Calculate actual progress based on world state
            results.append(ObjectiveProgress(
                objective_id=obj_id,
                name=obj["name"],
                description=obj["description"],
                progress=0.0,  # Will be calculated dynamically
                completed=False,
                points=obj["points"]
            ))

    return results


@router.post("/start")
async def start_scenario(request: StartScenarioRequest):
    """
    Start a new game with the specified scenario.
    In unified mode, applies directly to world state.
    """
    _ensure_scenarios_loaded()
    data = load_scenarios()

    # Find scenario
    scenario = None
    for s in data["scenarios"]:
        if s["id"] == request.scenario_id:
            scenario = s
            break

    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {request.scenario_id} not found")

    # Get difficulty modifiers
    difficulty = request.difficulty_override or scenario["difficulty"]
    modifiers = data.get("difficulty_modifiers", {}).get(difficulty, {})

    # If unified mode, apply scenario directly
    if is_unified_mode() and request.player_country:
        world = get_world()
        success = scenario_manager.start_scenario(
            request.scenario_id,
            world,
            request.player_country
        )

        if success:
            # Get active objectives
            objectives = [
                {
                    "id": obj["id"],
                    "name": obj["name"],
                    "description": obj["description"],
                    "type": obj["type"],
                    "points": obj["points"],
                    "status": obj["status"],
                    "progress": obj["progress"],
                }
                for obj in world.active_objectives
            ]

            return {
                "success": True,
                "message": f"Scenario '{scenario['name_fr']}' started",
                "unified_mode": True,
                "scenario_id": scenario["id"],
                "player_country": request.player_country,
                "start_year": world.year,
                "end_year": world.scenario_end_year,
                "objectives": objectives,
            }

    # Legacy mode: Return init data for frontend to apply
    init_data = {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name_fr"],
        "start_year": scenario["start_year"],
        "difficulty": difficulty,
        "difficulty_modifiers": modifiers,
        "initial_state": scenario.get("initial_state", {}),
        "active_conflicts": scenario.get("active_conflicts", []),
        "modified_countries": scenario.get("modified_countries", {}),
        "disabled_countries": scenario.get("disabled_countries", []),
        "blocs_override": scenario.get("blocs_override"),
        "currency_changes": scenario.get("currency_changes"),
        "global_effects": scenario.get("global_effects"),
        "player_country": request.player_country,
        "objectives": scenario.get("objectives", {}).get(request.player_country, []) if request.player_country else [],
        "duration": scenario.get("duration"),
        "special_events": scenario.get("special_events", [])
    }

    return {
        "success": True,
        "message": f"Scenario '{scenario['name_fr']}' initialized",
        "unified_mode": False,
        "init_data": init_data
    }


@router.get("/difficulty/modifiers")
async def get_difficulty_modifiers():
    """Get all difficulty modifiers"""
    data = load_scenarios()
    return data.get("difficulty_modifiers", {})


@router.get("/tags")
async def get_all_tags():
    """Get all unique tags used in scenarios"""
    data = load_scenarios()
    all_tags = set()
    for scenario in data["scenarios"]:
        all_tags.update(scenario.get("tags", []))
    return sorted(list(all_tags))


# ============================================================================
# CURRENT SCENARIO MANAGEMENT (Phase 14)
# ============================================================================

@router.get("/current/status")
async def get_current_scenario_status():
    """
    Get the status of the currently active scenario.
    Returns scenario info, objectives progress, and game state.
    """
    _ensure_scenarios_loaded()
    world = get_world()

    # Check if a scenario is active
    if not hasattr(world, "scenario_id") or not world.scenario_id:
        return {
            "active": False,
            "message": "No scenario currently active"
        }

    scenario = scenario_manager.get_scenario(world.scenario_id)
    if not scenario:
        return {
            "active": False,
            "message": f"Scenario {world.scenario_id} not found in manager"
        }

    # Get objectives with current progress
    objectives = []
    if hasattr(world, "active_objectives") and world.active_objectives:
        for obj in world.active_objectives:
            objectives.append({
                "id": obj.get("id"),
                "name": obj.get("name"),
                "description": obj.get("description"),
                "type": obj.get("type"),
                "points": obj.get("points", 0),
                "status": obj.get("status", "pending"),
                "progress": obj.get("progress", 0),
                "years_maintained": obj.get("years_maintained", 0),
            })

    # Calculate total score
    total_score = scenario_manager.get_scenario_score(world)
    is_complete = scenario_manager.is_scenario_complete(world)
    is_failed = scenario_manager.is_scenario_failed(world)

    return {
        "active": True,
        "scenario_id": world.scenario_id,
        "scenario_name": scenario.name_fr,
        "player_country": getattr(world, "player_country_id", None),
        "current_year": world.year,
        "start_year": scenario.start_year,
        "end_year": getattr(world, "scenario_end_year", None),
        "years_remaining": (world.scenario_end_year - world.year) if world.scenario_end_year else None,
        "objectives": objectives,
        "total_score": total_score,
        "max_possible_score": sum(obj.get("points", 0) for obj in objectives),
        "is_complete": is_complete,
        "is_failed": is_failed,
        "game_ended": getattr(world, "game_ended", False),
    }


@router.post("/current/check-objectives")
async def check_current_objectives():
    """
    Manually trigger objective checking and update progress.
    Returns list of objectives with status changes.
    """
    _ensure_scenarios_loaded()
    world = get_world()

    if not hasattr(world, "scenario_id") or not world.scenario_id:
        raise HTTPException(status_code=400, detail="No scenario currently active")

    # Check objectives and get changes
    changes = scenario_manager.check_objectives(world)

    # Get updated objectives
    objectives = []
    if hasattr(world, "active_objectives") and world.active_objectives:
        for obj in world.active_objectives:
            objectives.append({
                "id": obj.get("id"),
                "name": obj.get("name"),
                "status": obj.get("status"),
                "progress": obj.get("progress"),
                "points": obj.get("points", 0),
            })

    return {
        "checked": True,
        "changes": changes,
        "objectives": objectives,
        "total_score": scenario_manager.get_scenario_score(world),
        "is_complete": scenario_manager.is_scenario_complete(world),
        "is_failed": scenario_manager.is_scenario_failed(world),
    }


@router.post("/current/end")
async def end_current_scenario():
    """
    End the current scenario and calculate final score.
    """
    _ensure_scenarios_loaded()
    world = get_world()

    if not hasattr(world, "scenario_id") or not world.scenario_id:
        raise HTTPException(status_code=400, detail="No scenario currently active")

    scenario = scenario_manager.get_scenario(world.scenario_id)
    scenario_name = scenario.name_fr if scenario else world.scenario_id

    # Final objective check
    scenario_manager.check_objectives(world)

    # Calculate final score
    final_score = scenario_manager.get_scenario_score(world)
    is_complete = scenario_manager.is_scenario_complete(world)
    is_failed = scenario_manager.is_scenario_failed(world)

    # Determine outcome
    if is_complete:
        outcome = "victory"
        message = f"Felicitations ! Scenario '{scenario_name}' termine avec succes."
    elif is_failed:
        outcome = "defeat"
        message = f"Echec du scenario '{scenario_name}'."
    else:
        outcome = "incomplete"
        message = f"Scenario '{scenario_name}' termine avant completion."

    # Get final objectives state
    objectives = []
    if hasattr(world, "active_objectives") and world.active_objectives:
        for obj in world.active_objectives:
            objectives.append({
                "id": obj.get("id"),
                "name": obj.get("name"),
                "status": obj.get("status"),
                "progress": obj.get("progress"),
                "points": obj.get("points", 0),
            })

    # Clear scenario from world
    old_scenario_id = world.scenario_id
    world.scenario_id = None
    world.scenario_end_year = None
    world.active_objectives = []

    logger.info(f"Scenario ended: {old_scenario_id}, outcome={outcome}, score={final_score}")

    return {
        "ended": True,
        "scenario_id": old_scenario_id,
        "scenario_name": scenario_name,
        "outcome": outcome,
        "message": message,
        "final_score": final_score,
        "objectives": objectives,
        "years_played": world.year - (scenario.start_year if scenario else 2025),
    }
