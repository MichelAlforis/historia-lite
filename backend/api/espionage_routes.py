"""Espionage API routes - Intelligence operations and Fog of War"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.espionage import (
    espionage_manager,
    IntelQuality,
    SecretLevel,
    SpyMission,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/espionage", tags=["espionage"])


# ==================== Request/Response Models ====================

class StartMissionRequest(BaseModel):
    agent_country: str
    target_country: str
    mission_type: str = Field(
        description="Type: recon, deep_intel, sabotage, steal_tech, counter_intel"
    )


class IntelRequest(BaseModel):
    observer_country: str
    target_country: str


# ==================== Mission Management Endpoints ====================

@router.get("/status")
async def get_espionage_status():
    """Get global espionage status and active operations"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    operations = [
        {
            "id": op.id,
            "agent_country": op.agent_country,
            "target_country": op.target_country,
            "mission_type": op.mission_type,
            "progress": op.progress,
            "success_chance": op.success_chance,
            "started_year": op.started_year,
        }
        for op in espionage_manager.operations
    ]

    return {
        "status": "active" if operations else "inactive",
        "operations": operations,
        "total_operations": len(operations),
        "year": world.year,
    }


@router.post("/mission/start")
async def start_spy_mission(request: StartMissionRequest):
    """Start a new espionage mission against a target country"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    agent = world.get_country(request.agent_country)
    target = world.get_country(request.target_country)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent country {request.agent_country} not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Target country {request.target_country} not found")

    # Check if mission already exists
    existing = [
        op for op in espionage_manager.operations
        if op.agent_country == request.agent_country
        and op.target_country == request.target_country
    ]
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Mission already active against {request.target_country}"
        )

    # Validate mission type
    valid_types = ["recon", "deep_intel", "sabotage", "steal_tech", "counter_intel"]
    if request.mission_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mission type. Must be one of: {valid_types}"
        )

    mission = espionage_manager.start_mission(
        agent_id=request.agent_country,
        target_id=request.target_country,
        mission_type=request.mission_type,
        world=world,
    )

    if not mission:
        raise HTTPException(status_code=400, detail="Failed to start mission")

    mission_descriptions = {
        "recon": "Reconnaissance - gather basic intel",
        "deep_intel": "Deep Intelligence - detailed analysis",
        "sabotage": "Sabotage - damage infrastructure",
        "steal_tech": "Technology Theft - acquire secrets",
        "counter_intel": "Counter-Intelligence - expose foreign agents",
    }

    return {
        "success": True,
        "mission": {
            "id": mission.id,
            "agent_country": mission.agent_country,
            "target_country": mission.target_country,
            "mission_type": mission.mission_type,
            "success_chance": mission.success_chance,
            "started_year": mission.started_year,
        },
        "description": mission_descriptions.get(request.mission_type, "Unknown mission"),
        "message_fr": f"Operation d'espionnage lancee contre {target.name_fr}",
    }


@router.get("/missions/{country_id}")
async def get_country_missions(country_id: str):
    """Get all espionage missions for a country (as agent or target)"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    as_agent = [
        {
            "id": op.id,
            "target_country": op.target_country,
            "mission_type": op.mission_type,
            "progress": op.progress,
            "success_chance": op.success_chance,
        }
        for op in espionage_manager.operations
        if op.agent_country == country_id
    ]

    as_target = [
        {
            "id": op.id,
            "agent_country": op.agent_country,
            "mission_type": op.mission_type,
            "progress": op.progress,
        }
        for op in espionage_manager.operations
        if op.target_country == country_id
    ]

    return {
        "country_id": country_id,
        "missions_as_agent": as_agent,
        "missions_as_target": as_target,
        "total_active": len(as_agent),
        "total_targeted": len(as_target),
    }


@router.delete("/mission/{mission_id}")
async def cancel_mission(mission_id: str):
    """Cancel an active espionage mission"""
    mission = next(
        (op for op in espionage_manager.operations if op.id == mission_id),
        None
    )

    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    espionage_manager.operations.remove(mission)

    return {
        "success": True,
        "message": f"Mission {mission_id} cancelled",
        "message_fr": f"Operation {mission_id} annulee",
    }


# ==================== Intelligence Gathering Endpoints ====================

@router.get("/intel/{observer_id}/{target_id}")
async def get_intel_on_country(observer_id: str, target_id: str):
    """Get intelligence report on a target country from observer's perspective"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    observer = world.get_country(observer_id)
    target = world.get_country(target_id)

    if not observer:
        raise HTTPException(status_code=404, detail=f"Observer {observer_id} not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Target {target_id} not found")

    # Calculate intel score
    intel_score = espionage_manager.get_intel_score(observer, target, world)
    intel_quality = espionage_manager.get_intel_quality(intel_score)

    # Get target data with fog of war applied
    target_data = target.model_dump() if hasattr(target, 'model_dump') else target.__dict__.copy()
    filtered_data = espionage_manager.apply_fog_of_war(target_data, intel_score)

    # Nuclear special handling
    nuclear_info = espionage_manager.get_nuclear_display(target, intel_score)

    return {
        "observer_id": observer_id,
        "target_id": target_id,
        "intel_score": intel_score,
        "intel_quality": intel_quality.value,
        "data": filtered_data,
        "nuclear_assessment": nuclear_info,
        "analysis": _get_intel_analysis(intel_quality, target),
    }


@router.get("/intel/{observer_id}/summary")
async def get_intel_summary(observer_id: str):
    """Get intelligence summary for all known countries"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    observer = world.get_country(observer_id)
    if not observer:
        raise HTTPException(status_code=404, detail=f"Observer {observer_id} not found")

    summaries = []

    for country in world.get_all_countries():
        if country.id == observer_id:
            continue

        intel_score = espionage_manager.get_intel_score(observer, country, world)
        intel_quality = espionage_manager.get_intel_quality(intel_score)

        summaries.append({
            "country_id": country.id,
            "name": country.name,
            "name_fr": country.name_fr,
            "tier": country.tier,
            "intel_score": intel_score,
            "intel_quality": intel_quality.value,
            "is_ally": country.id in observer.allies,
            "is_rival": country.id in observer.rivals,
            "at_war": country.id in observer.at_war,
        })

    # Sort by intel quality
    summaries.sort(key=lambda x: x["intel_score"], reverse=True)

    return {
        "observer_id": observer_id,
        "summaries": summaries,
        "total_countries": len(summaries),
        "excellent_intel": len([s for s in summaries if s["intel_quality"] in ["excellent", "perfect"]]),
        "poor_intel": len([s for s in summaries if s["intel_quality"] in ["none", "partial"]]),
    }


# ==================== Secret Levels Reference ====================

@router.get("/secret-levels")
async def get_secret_levels():
    """Get reference data for secret classification levels"""
    from engine.espionage import INFO_SECRET_LEVELS

    levels = {
        "PUBLIC": {"value": 0, "description": "Publicly available information"},
        "LOW": {"value": 20, "description": "Requires basic intelligence"},
        "MEDIUM": {"value": 40, "description": "Requires good intelligence network"},
        "HIGH": {"value": 60, "description": "Military secrets, requires excellent intel"},
        "TOP_SECRET": {"value": 80, "description": "Nuclear and covert operations"},
    }

    field_classifications = {
        field: {"level": level.name, "required_score": level.value}
        for field, level in INFO_SECRET_LEVELS.items()
    }

    return {
        "levels": levels,
        "field_classifications": field_classifications,
    }


@router.get("/mission-types")
async def get_mission_types():
    """Get reference data for available mission types"""
    return {
        "mission_types": [
            {
                "id": "recon",
                "name": "Reconnaissance",
                "name_fr": "Reconnaissance",
                "description": "Gather basic information about target",
                "duration": "1-2 years",
                "risk": "low",
                "intel_boost": 10,
            },
            {
                "id": "deep_intel",
                "name": "Deep Intelligence",
                "name_fr": "Renseignement approfondi",
                "description": "Detailed analysis of military and economic capabilities",
                "duration": "2-3 years",
                "risk": "medium",
                "intel_boost": 25,
            },
            {
                "id": "sabotage",
                "name": "Sabotage",
                "name_fr": "Sabotage",
                "description": "Damage infrastructure or military assets",
                "duration": "1-2 years",
                "risk": "high",
                "effects": "Target loses 5-15 economy or military",
            },
            {
                "id": "steal_tech",
                "name": "Technology Theft",
                "name_fr": "Vol de technologie",
                "description": "Acquire technological secrets",
                "duration": "2-4 years",
                "risk": "very_high",
                "effects": "Agent gains 5-10 technology",
            },
            {
                "id": "counter_intel",
                "name": "Counter-Intelligence",
                "name_fr": "Contre-espionnage",
                "description": "Identify and expose foreign agents",
                "duration": "1-2 years",
                "risk": "medium",
                "effects": "Cancel enemy operations, improve relations with target",
            },
        ]
    }


# ==================== Helper Functions ====================

def _get_world():
    """Get the current world state"""
    try:
        from api.game_state import get_world
        return get_world()
    except ImportError as e:
        logger.warning(f"Could not import game_state: {e}")
    return None


def _get_intel_analysis(quality: IntelQuality, target) -> dict:
    """Generate analysis text based on intel quality"""
    analyses = {
        IntelQuality.NONE: {
            "summary": "Minimal information available",
            "summary_fr": "Information minimale disponible",
            "recommendation": "Increase intelligence operations",
        },
        IntelQuality.PARTIAL: {
            "summary": "Basic economic data available",
            "summary_fr": "Donnees economiques de base disponibles",
            "recommendation": "Launch deep intel mission for military data",
        },
        IntelQuality.GOOD: {
            "summary": "Good overview of civilian sectors",
            "summary_fr": "Bonne vue d'ensemble des secteurs civils",
            "recommendation": "Military capabilities still partially obscured",
        },
        IntelQuality.VERY_GOOD: {
            "summary": "Comprehensive intelligence picture",
            "summary_fr": "Image de renseignement complete",
            "recommendation": "Nuclear status may require confirmation",
        },
        IntelQuality.EXCELLENT: {
            "summary": "Detailed military and nuclear assessment",
            "summary_fr": "Evaluation militaire et nucleaire detaillee",
            "recommendation": "Maintain intelligence network",
        },
        IntelQuality.PERFECT: {
            "summary": "Complete situational awareness",
            "summary_fr": "Conscience situationnelle complete",
            "recommendation": "All data confirmed and accurate",
        },
    }

    return analyses.get(quality, analyses[IntelQuality.NONE])
