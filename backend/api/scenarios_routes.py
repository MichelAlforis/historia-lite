"""
Historia Lite - Scenarios & Objectives API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from pathlib import Path

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])

# Data paths
DATA_DIR = Path(__file__).parent.parent / "data"
SCENARIOS_FILE = DATA_DIR / "scenarios.json"


def load_scenarios() -> dict:
    """Load scenarios from JSON file"""
    if SCENARIOS_FILE.exists():
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scenarios": [], "objectives_catalog": {}, "difficulty_modifiers": {}}


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

@router.get("/", response_model=List[ScenarioSummary])
async def list_scenarios():
    """List all available scenarios"""
    data = load_scenarios()
    return [
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
    Returns the modified world state to apply.
    """
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

    # Build initialization data
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
