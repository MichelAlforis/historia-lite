"""Scenario API routes for Historia Lite - Phase 14"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from engine.scenario import scenario_manager, Scenario, ActiveObjective, ObjectiveStatus
from api.game_state import get_world, get_data_dir, is_unified_mode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


# Response models
class ScenarioListItem(BaseModel):
    """Scenario summary for listing"""
    id: str
    name: str
    name_fr: str
    description: str
    start_year: int
    duration: Optional[int]
    difficulty: str
    icon: str
    tags: List[str]
    recommended_countries: List[str]


class ScenarioDetailResponse(BaseModel):
    """Full scenario details"""
    id: str
    name: str
    name_fr: str
    description: str
    description_fr: str
    start_year: int
    duration: Optional[int]
    end_year: Optional[int]
    difficulty: str
    icon: str
    tags: List[str]
    recommended_countries: List[str]
    objectives_by_country: dict
    initial_state: dict
    customizable: bool


class ObjectiveResponse(BaseModel):
    """Objective details"""
    id: str
    name: str
    description: str
    type: str
    difficulty: str
    points: int


class ActiveObjectiveResponse(BaseModel):
    """Active objective with progress"""
    id: str
    country_id: str
    name: str
    description: str
    type: str
    points: int
    status: str
    progress: int


class StartScenarioRequest(BaseModel):
    """Request to start a scenario"""
    scenario_id: str
    player_country: str = "USA"


class StartScenarioResponse(BaseModel):
    """Response after starting a scenario"""
    success: bool
    scenario_id: str
    scenario_name: str
    player_country: str
    start_year: int
    end_year: Optional[int]
    objectives: List[ActiveObjectiveResponse]
    message: str


class ScenarioStatusResponse(BaseModel):
    """Current scenario status"""
    active: bool
    scenario_id: Optional[str]
    scenario_name: Optional[str]
    player_country: Optional[str]
    current_year: int
    end_year: Optional[int]
    objectives: List[ActiveObjectiveResponse]
    score: int
    is_complete: bool
    is_failed: bool


# Ensure scenarios are loaded
def _ensure_scenarios_loaded():
    """Ensure scenarios are loaded from disk"""
    if not scenario_manager._scenarios:
        data_dir = get_data_dir()
        scenario_manager.load_scenarios(data_dir)


@router.get("", response_model=List[ScenarioListItem])
async def list_scenarios(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
):
    """Get list of available scenarios"""
    _ensure_scenarios_loaded()

    scenarios = scenario_manager.get_all_scenarios()

    # Apply filters
    if difficulty:
        scenarios = [s for s in scenarios if s.difficulty == difficulty]
    if tag:
        scenarios = [s for s in scenarios if tag in s.tags]

    return [
        ScenarioListItem(
            id=s.id,
            name=s.name,
            name_fr=s.name_fr,
            description=s.description,
            start_year=s.start_year,
            duration=s.duration,
            difficulty=s.difficulty,
            icon=s.icon,
            tags=s.tags,
            recommended_countries=s.recommended_countries,
        )
        for s in scenarios
    ]


@router.get("/objectives", response_model=List[ObjectiveResponse])
async def list_objectives():
    """Get the objectives catalog"""
    _ensure_scenarios_loaded()

    catalog = scenario_manager.get_objectives_catalog()
    return [
        ObjectiveResponse(
            id=obj_id,
            name=entry.name,
            description=entry.description,
            type=entry.type,
            difficulty=entry.difficulty,
            points=entry.points,
        )
        for obj_id, entry in catalog.items()
    ]


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario(scenario_id: str):
    """Get detailed information about a specific scenario"""
    _ensure_scenarios_loaded()

    scenario = scenario_manager.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found")

    return ScenarioDetailResponse(
        id=scenario.id,
        name=scenario.name,
        name_fr=scenario.name_fr,
        description=scenario.description,
        description_fr=scenario.description_fr,
        start_year=scenario.start_year,
        duration=scenario.duration,
        end_year=scenario.end_year,
        difficulty=scenario.difficulty,
        icon=scenario.icon,
        tags=scenario.tags,
        recommended_countries=scenario.recommended_countries,
        objectives_by_country=scenario.objectives,
        initial_state=scenario.initial_state,
        customizable=scenario.customizable,
    )


@router.post("/start", response_model=StartScenarioResponse)
async def start_scenario(request: StartScenarioRequest):
    """Start a new scenario"""
    _ensure_scenarios_loaded()

    # Verify unified mode is enabled
    if not is_unified_mode():
        raise HTTPException(
            status_code=400,
            detail="Scenarios require unified mode. Enable with POST /api/unified-mode?enabled=true"
        )

    world = get_world()
    scenario = scenario_manager.get_scenario(request.scenario_id)

    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario {request.scenario_id} not found")

    # Check if country is recommended
    if request.player_country not in scenario.recommended_countries:
        logger.warning(f"Player chose non-recommended country: {request.player_country}")

    # Start the scenario
    success = scenario_manager.start_scenario(
        request.scenario_id,
        world,
        request.player_country
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start scenario")

    # Get active objectives
    objectives = [
        ActiveObjectiveResponse(
            id=obj["id"],
            country_id=obj["country_id"],
            name=obj["name"],
            description=obj["description"],
            type=obj["type"],
            points=obj["points"],
            status=obj["status"],
            progress=obj["progress"],
        )
        for obj in world.active_objectives
    ]

    return StartScenarioResponse(
        success=True,
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        player_country=request.player_country,
        start_year=scenario.start_year,
        end_year=scenario.end_year,
        objectives=objectives,
        message=f"Started scenario: {scenario.name_fr}",
    )


@router.get("/current/status", response_model=ScenarioStatusResponse)
async def get_scenario_status():
    """Get status of current active scenario"""
    world = get_world()

    if not world.scenario_id:
        return ScenarioStatusResponse(
            active=False,
            scenario_id=None,
            scenario_name=None,
            player_country=None,
            current_year=world.year,
            end_year=None,
            objectives=[],
            score=0,
            is_complete=False,
            is_failed=False,
        )

    _ensure_scenarios_loaded()
    scenario = scenario_manager.get_scenario(world.scenario_id)

    objectives = [
        ActiveObjectiveResponse(
            id=obj["id"],
            country_id=obj["country_id"],
            name=obj["name"],
            description=obj["description"],
            type=obj["type"],
            points=obj["points"],
            status=obj["status"],
            progress=obj["progress"],
        )
        for obj in world.active_objectives
    ]

    return ScenarioStatusResponse(
        active=True,
        scenario_id=world.scenario_id,
        scenario_name=scenario.name if scenario else "Unknown",
        player_country=world.player_country_id,
        current_year=world.year,
        end_year=world.scenario_end_year,
        objectives=objectives,
        score=scenario_manager.get_scenario_score(world),
        is_complete=scenario_manager.is_scenario_complete(world),
        is_failed=scenario_manager.is_scenario_failed(world),
    )


@router.post("/current/check-objectives")
async def check_objectives():
    """Manually check and update all objectives"""
    world = get_world()

    if not world.scenario_id:
        raise HTTPException(status_code=400, detail="No active scenario")

    _ensure_scenarios_loaded()
    changes = scenario_manager.check_objectives(world)

    return {
        "checked": len(world.active_objectives),
        "changes": changes,
        "score": scenario_manager.get_scenario_score(world),
        "is_complete": scenario_manager.is_scenario_complete(world),
        "is_failed": scenario_manager.is_scenario_failed(world),
    }


@router.post("/current/end")
async def end_scenario():
    """End the current scenario"""
    world = get_world()

    if not world.scenario_id:
        raise HTTPException(status_code=400, detail="No active scenario")

    _ensure_scenarios_loaded()

    # Calculate final score
    final_score = scenario_manager.get_scenario_score(world)
    is_complete = scenario_manager.is_scenario_complete(world)

    # Clear scenario from world
    scenario_id = world.scenario_id
    world.scenario_id = None
    world.scenario_end_year = None
    world.player_country_id = None
    world.active_objectives = []

    return {
        "ended": True,
        "scenario_id": scenario_id,
        "final_score": final_score,
        "completed_all_objectives": is_complete,
        "final_year": world.year,
    }
