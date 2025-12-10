"""Projects and dilemmas routes for Historia Lite"""
import logging
import json
import re
from typing import Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from schemas.interaction import (
    ProjectListResponse,
    ProjectResponse,
    ProjectTemplate,
    CustomProjectRequest,
    PendingDilemmasResponse,
    DilemmaResolveRequest,
    DilemmaResolveResponse,
    DilemmaHistoryResponse,
)
from engine.project import project_manager
from engine.dilemma import dilemma_manager
from api.game_state import get_world, get_ollama, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["projects"])


# ============================================================================
# PROJECT ENDPOINTS
# ============================================================================

@router.get("/projects/{country_id}", response_model=ProjectListResponse)
async def get_country_projects(country_id: str):
    """Get all active and available projects for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    active_projects = world.active_projects.get(country_id.upper(), [])
    available = project_manager.get_available_projects(country)

    return ProjectListResponse(
        country_id=country_id.upper(),
        active_projects=active_projects,
        available_projects=available
    )


@router.post("/projects/{country_id}/start/{project_id}")
async def start_project(country_id: str, project_id: str):
    """Start a new project for a country"""
    from engine.social_reactions import apply_project_social_effects

    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    active_projects = world.active_projects.get(country_id.upper(), [])

    can_start, reason = project_manager.can_start_project(
        project_id, country, active_projects
    )

    if not can_start:
        raise HTTPException(status_code=400, detail=reason)

    new_project = project_manager.start_project(project_id, country_id.upper())
    if not new_project:
        raise HTTPException(status_code=404, detail=f"Project template {project_id} not found")

    if country_id.upper() not in world.active_projects:
        world.active_projects[country_id.upper()] = []
    world.active_projects[country_id.upper()].append(new_project)

    all_templates = project_manager.get_all_templates()
    template = all_templates.get(project_id)
    if template and template.social_tags:
        social_events = apply_project_social_effects(template, country, world)
        for event in social_events:
            world.global_events.append(event)

    next_milestone = None
    if template and template.milestones:
        next_milestone = template.milestones[0]

    return ProjectResponse(
        project=new_project,
        next_milestone=next_milestone,
        years_remaining=new_project.total_years,
        completion_year=world.year + new_project.total_years
    )


@router.post("/projects/{country_id}/cancel/{project_id}")
async def cancel_project(country_id: str, project_id: str):
    """Cancel an active project"""
    world = get_world()

    active_projects = world.active_projects.get(country_id.upper(), [])

    for project in active_projects:
        if project.id == project_id or project.template_id == project_id:
            project_manager.cancel_project(project)
            return {"status": "cancelled", "project_id": project.id}

    raise HTTPException(
        status_code=404,
        detail=f"Active project {project_id} not found for {country_id}"
    )


@router.post("/projects/{country_id}/accelerate/{project_id}")
async def accelerate_project(country_id: str, project_id: str):
    """Accelerate a project (costs extra economy)"""
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    active_projects = world.active_projects.get(country_id.upper(), [])

    for project in active_projects:
        if project.id == project_id or project.template_id == project_id:
            success = project_manager.accelerate_project(project, country)
            if success:
                return {"status": "accelerated", "project_id": project.id}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient economy to accelerate project"
                )

    raise HTTPException(
        status_code=404,
        detail=f"Active project {project_id} not found for {country_id}"
    )


@router.post("/projects/create-custom", response_model=ProjectTemplate)
async def create_custom_project(request: CustomProjectRequest):
    """Create a custom player-defined project."""
    valid_effects = {"economy", "military", "stability", "soft_power", "technology", "resources", "nuclear"}
    for key, value in request.completion_effects.items():
        if key not in valid_effects:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid effect key: {key}. Valid keys: {valid_effects}"
            )
        if value < -20 or value > 30:
            raise HTTPException(
                status_code=400,
                detail=f"Effect value for {key} must be between -20 and +30"
            )

    template = project_manager.create_custom_project(
        name=request.name,
        name_fr=request.name_fr,
        description=request.description,
        description_fr=request.description_fr,
        project_type=request.project_type,
        total_years=request.total_years,
        economy_cost_per_year=request.economy_cost_per_year,
        completion_effects=request.completion_effects,
        technology_required=request.technology_required
    )

    return template


class ProjectSuggestionRequest(BaseModel):
    """Request to get AI-suggested parameters for a project"""
    description: str = Field(..., min_length=10, description="Natural language description of the project")
    description_fr: str = Field(default="", description="Description in French (optional)")


class ProjectSuggestionResponse(BaseModel):
    """AI-suggested project parameters"""
    suggested_name: str
    suggested_name_fr: str
    suggested_type: str
    suggested_years: int
    suggested_cost: int
    suggested_effects: Dict[str, int]
    explanation: str
    explanation_fr: str


@router.post("/projects/suggest", response_model=ProjectSuggestionResponse)
async def suggest_project_parameters(request: ProjectSuggestionRequest):
    """Use AI to suggest project parameters from a description."""
    settings = get_settings()
    ollama = get_ollama()
    use_ollama = settings.ai_mode == "ollama" and ollama

    if use_ollama:
        prompt = f"""Analyse ce projet gouvernemental et suggere des parametres realistes.

Description du projet: {request.description}

Reponds UNIQUEMENT en JSON valide avec cette structure exacte:
{{
    "name": "nom anglais court",
    "name_fr": "nom francais court",
    "type": "social|economic|military|technology|infrastructure|space|nuclear",
    "years": 3-15,
    "cost": 1-10,
    "effects": {{
        "stability": -20 a +20,
        "soft_power": -10 a +15,
        "economy": -10 a +15,
        "technology": -5 a +20,
        "military": -5 a +10
    }},
    "explanation": "courte explication anglais",
    "explanation_fr": "courte explication francais"
}}

Regles:
- Projets sociaux (cancer, droits, education) = stability +5-15, soft_power +5-10
- Projets economiques = economy +10-15, stability +/-5
- Projets militaires = military +10-20, economy -5
- Projets tech = technology +10-20, economy +5
- Duree: petits projets 3-5 ans, moyens 5-8 ans, grands 8-15 ans
- Cout: petits 1-3, moyens 3-5, grands 5-10
"""

        try:
            response = await ollama.generate(prompt)
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return ProjectSuggestionResponse(
                    suggested_name=data.get("name", request.description[:30]),
                    suggested_name_fr=data.get("name_fr", request.description_fr[:30] if request.description_fr else request.description[:30]),
                    suggested_type=data.get("type", "social"),
                    suggested_years=data.get("years", 5),
                    suggested_cost=data.get("cost", 3),
                    suggested_effects=data.get("effects", {"stability": 10}),
                    explanation=data.get("explanation", ""),
                    explanation_fr=data.get("explanation_fr", "")
                )
        except Exception as e:
            logger.warning(f"Ollama suggestion failed: {e}, falling back to algorithmic")

    # Fallback: algorithmic estimation based on keywords
    return _suggest_project_algorithmic(request)


def _suggest_project_algorithmic(request: ProjectSuggestionRequest) -> ProjectSuggestionResponse:
    """Algorithmic fallback for project suggestion"""
    desc_lower = request.description.lower()

    if any(word in desc_lower for word in ["cancer", "sante", "health", "maladie", "hopital", "medical"]):
        return ProjectSuggestionResponse(
            suggested_name="Health Initiative",
            suggested_name_fr="Initiative Sante",
            suggested_type="social",
            suggested_years=8,
            suggested_cost=5,
            suggested_effects={"stability": 10, "soft_power": 5, "technology": 3},
            explanation="Healthcare projects improve stability through better public health",
            explanation_fr="Les projets de sante ameliorent la stabilite grace a une meilleure sante publique"
        )
    elif any(word in desc_lower for word in ["mariage", "droits", "rights", "egalite", "equality", "lgbtq", "feminic", "femme", "women"]):
        return ProjectSuggestionResponse(
            suggested_name="Social Rights Reform",
            suggested_name_fr="Reforme des Droits Sociaux",
            suggested_type="social",
            suggested_years=3,
            suggested_cost=2,
            suggested_effects={"stability": 5, "soft_power": 12},
            explanation="Social rights reforms significantly boost soft power internationally",
            explanation_fr="Les reformes de droits sociaux augmentent significativement le soft power"
        )
    elif any(word in desc_lower for word in ["education", "ecole", "school", "universite"]):
        return ProjectSuggestionResponse(
            suggested_name="Education Reform",
            suggested_name_fr="Reforme Education",
            suggested_type="social",
            suggested_years=6,
            suggested_cost=4,
            suggested_effects={"technology": 8, "stability": 5, "soft_power": 3},
            explanation="Education improves technology and long-term stability",
            explanation_fr="L'education ameliore la technologie et la stabilite a long terme"
        )
    elif any(word in desc_lower for word in ["armee", "military", "defense", "arme", "weapon"]):
        return ProjectSuggestionResponse(
            suggested_name="Defense Modernization",
            suggested_name_fr="Modernisation Defense",
            suggested_type="military",
            suggested_years=5,
            suggested_cost=6,
            suggested_effects={"military": 15, "technology": 5},
            explanation="Military projects boost defense capabilities",
            explanation_fr="Les projets militaires renforcent les capacites de defense"
        )
    elif any(word in desc_lower for word in ["climat", "climate", "vert", "green", "energie", "energy", "renouvelable"]):
        return ProjectSuggestionResponse(
            suggested_name="Green Transition",
            suggested_name_fr="Transition Verte",
            suggested_type="economic",
            suggested_years=8,
            suggested_cost=5,
            suggested_effects={"resources": 10, "soft_power": 8, "economy": 5},
            explanation="Environmental projects improve resources and international image",
            explanation_fr="Les projets environnementaux ameliorent les ressources et l'image internationale"
        )
    else:
        return ProjectSuggestionResponse(
            suggested_name="National Initiative",
            suggested_name_fr="Initiative Nationale",
            suggested_type="social",
            suggested_years=5,
            suggested_cost=3,
            suggested_effects={"stability": 8, "soft_power": 5},
            explanation="General improvement project for the country",
            explanation_fr="Projet d'amelioration generale pour le pays"
        )


# ============================================================================
# DILEMMA ENDPOINTS
# ============================================================================

@router.get("/dilemmas/{country_id}/pending", response_model=PendingDilemmasResponse)
async def get_pending_dilemmas(country_id: str):
    """Get all pending dilemmas for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    pending = dilemma_manager.get_pending_dilemmas(country_id.upper())

    return PendingDilemmasResponse(
        country_id=country_id.upper(),
        pending_dilemmas=pending,
        count=len(pending)
    )


@router.post("/dilemmas/resolve", response_model=DilemmaResolveResponse)
async def resolve_dilemma(request: DilemmaResolveRequest):
    """Resolve a pending dilemma with player's choice"""
    world = get_world()
    country = world.get_country(request.player_country_id.upper())

    if not country:
        raise HTTPException(
            status_code=404,
            detail=f"Country {request.player_country_id} not found"
        )

    result = dilemma_manager.resolve_dilemma(
        dilemma_id=request.dilemma_id,
        choice_id=request.choice_id,
        country=country,
        world=world
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Failed to resolve dilemma - invalid dilemma_id or choice"
        )

    return result


@router.get("/dilemmas/{country_id}/history", response_model=DilemmaHistoryResponse)
async def get_dilemma_history(country_id: str):
    """Get history of resolved dilemmas for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    history = dilemma_manager.get_dilemma_history(country_id.upper())

    return DilemmaHistoryResponse(
        country_id=country_id.upper(),
        resolved_dilemmas=history,
        total=len(history)
    )


@router.post("/dilemmas/detect/{country_id}")
async def detect_dilemmas(country_id: str):
    """Manually trigger dilemma detection for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    active_projects = world.active_projects.get(country_id.upper(), [])

    new_dilemmas = dilemma_manager.detect_dilemmas(
        country=country,
        world=world,
        active_projects=active_projects
    )

    return {
        "detected": len(new_dilemmas),
        "dilemmas": [
            {"id": d.id, "title": d.title, "title_fr": d.title_fr}
            for d in new_dilemmas
        ]
    }
