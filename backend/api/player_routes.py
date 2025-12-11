"""Player and command routes for Historia Lite"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas.interaction import (
    CommandRequest,
    CommandResponse,
    CommandConfirmRequest,
)
from ai.command_interpreter import CommandInterpreter
from ai.strategic_ai import StrategicAI, get_geopolitical_analysis
from api.game_state import get_world, get_ollama, get_settings
from engine.consequences import consequence_calculator, ConsequencePrediction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["player"])

# Global command interpreter
_command_interpreter: Optional[CommandInterpreter] = None


def get_command_interpreter() -> CommandInterpreter:
    """Get or initialize command interpreter"""
    global _command_interpreter
    if _command_interpreter is None:
        ollama = get_ollama()
        _command_interpreter = CommandInterpreter(ollama)
    return _command_interpreter


@router.post("/player/select/{country_id}")
async def select_player_country(country_id: str):
    """Select a country as the player country"""
    world = get_world()
    country_id_upper = country_id.upper()

    for c in world.countries.values():
        c.is_player = False

    country = world.get_country(country_id_upper)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    country.is_player = True

    return {
        "status": "success",
        "player_country_id": country_id_upper,
        "player_country_name": country.name,
        "player_country_name_fr": country.name_fr
    }


@router.get("/player")
async def get_player_country():
    """Get the current player country"""
    world = get_world()

    for c in world.countries.values():
        if c.is_player:
            return {
                "player_country_id": c.id,
                "player_country_name": c.name,
                "player_country_name_fr": c.name_fr
            }

    return {"player_country_id": None, "message": "No player country selected"}


@router.post("/command", response_model=CommandResponse)
async def interpret_command(request: CommandRequest):
    """
    Interpret a natural language command from the player.
    Returns interpretation and asks for confirmation before execution.
    """
    world = get_world()
    country = world.get_country(request.player_country_id.upper())

    if not country:
        raise HTTPException(
            status_code=404,
            detail=f"Country {request.player_country_id} not found"
        )

    if not country.is_player:
        raise HTTPException(
            status_code=403,
            detail=f"Country {request.player_country_id} is not a player country"
        )

    settings = get_settings()
    interpreter = get_command_interpreter()
    use_ollama = settings.ai_mode == "ollama"

    response = await interpreter.interpret(
        command=request.command,
        country=country,
        world=world,
        use_ollama=use_ollama
    )

    return response


@router.post("/command/confirm", response_model=CommandResponse)
async def confirm_command(request: CommandConfirmRequest):
    """
    Confirm and execute a pending command.
    """
    world = get_world()
    country = world.get_country(request.player_country_id.upper())

    if not country:
        raise HTTPException(
            status_code=404,
            detail=f"Country {request.player_country_id} not found"
        )

    interpreter = get_command_interpreter()

    # Check if command exists
    if request.command_id not in interpreter.pending_commands:
        raise HTTPException(
            status_code=404,
            detail=f"Command {request.command_id} not found or already executed"
        )

    # Get the pending response
    pending_response = interpreter.pending_commands[request.command_id]

    # Store player_id in interpretation parameters for execute()
    pending_response.interpretation.parameters["player_id"] = request.player_country_id.upper()

    # Execute the command
    success, events = await interpreter.execute(
        command_id=request.command_id,
        world=world
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to execute command {request.command_id}"
        )

    # Return updated response with execution status
    return CommandResponse(
        command_id=request.command_id,
        original_command=pending_response.original_command,
        interpreted_as=pending_response.interpreted_as,
        interpretation=pending_response.interpretation,
        feasible=True,
        cost=pending_response.cost,
        requires_confirmation=False,
        confirmation_message=pending_response.confirmation_message,
        confirmation_message_fr=pending_response.confirmation_message_fr,
        executed=True,
        events=[{"id": e.id, "type": e.type, "title": e.title} for e in events]
    )


# Consequence Prediction Request Models
class PredictMilitaryBaseRequest(BaseModel):
    player_country_id: str
    target_zone_id: str


class PredictCulturalProgramRequest(BaseModel):
    player_country_id: str
    target_zone_id: str
    program_type: str


class PredictArmsSaleRequest(BaseModel):
    player_country_id: str
    target_country_id: str


class PredictSanctionsRequest(BaseModel):
    player_country_id: str
    target_country_id: str


class PredictWarRequest(BaseModel):
    player_country_id: str
    target_country_id: str


@router.post("/predict/military-base", response_model=ConsequencePrediction)
async def predict_military_base(request: PredictMilitaryBaseRequest):
    """Predict consequences of establishing a military base"""
    world = get_world()
    player = world.get_country(request.player_country_id.upper())

    if not player:
        raise HTTPException(status_code=404, detail=f"Country {request.player_country_id} not found")

    return consequence_calculator.predict_military_base(
        player, request.target_zone_id, world
    )


@router.post("/predict/cultural-program", response_model=ConsequencePrediction)
async def predict_cultural_program(request: PredictCulturalProgramRequest):
    """Predict consequences of launching a cultural program"""
    world = get_world()
    player = world.get_country(request.player_country_id.upper())

    if not player:
        raise HTTPException(status_code=404, detail=f"Country {request.player_country_id} not found")

    return consequence_calculator.predict_cultural_program(
        player, request.target_zone_id, request.program_type, world
    )


@router.post("/predict/arms-sale", response_model=ConsequencePrediction)
async def predict_arms_sale(request: PredictArmsSaleRequest):
    """Predict consequences of selling arms"""
    world = get_world()
    player = world.get_country(request.player_country_id.upper())

    if not player:
        raise HTTPException(status_code=404, detail=f"Country {request.player_country_id} not found")

    return consequence_calculator.predict_arms_sale(
        player, request.target_country_id.upper(), world
    )


@router.post("/predict/sanctions", response_model=ConsequencePrediction)
async def predict_sanctions(request: PredictSanctionsRequest):
    """Predict consequences of imposing sanctions"""
    world = get_world()
    player = world.get_country(request.player_country_id.upper())

    if not player:
        raise HTTPException(status_code=404, detail=f"Country {request.player_country_id} not found")

    return consequence_calculator.predict_sanctions(
        player, request.target_country_id.upper(), world
    )


@router.post("/predict/war", response_model=ConsequencePrediction)
async def predict_war(request: PredictWarRequest):
    """Predict consequences of declaring war"""
    world = get_world()
    player = world.get_country(request.player_country_id.upper())

    if not player:
        raise HTTPException(status_code=404, detail=f"Country {request.player_country_id} not found")

    return consequence_calculator.predict_war_declaration(
        player, request.target_country_id.upper(), world
    )


# ============================================================================
# STRATEGIC ADVICE
# ============================================================================

class StrategicAdviceResponse(BaseModel):
    """Response model for strategic advice"""
    country_id: str
    strategic_goal: str
    strategic_goal_fr: str
    power_rank: int
    total_countries: int
    threats: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    diplomatic_summary: Dict[str, Any]
    ollama_advice: Optional[str] = None
    ollama_available: bool = False


# French translations for strategic goals
GOAL_TRANSLATIONS = {
    "regional_hegemony": "Hegemonie regionale",
    "global_power": "Puissance mondiale",
    "economic_dominance": "Domination economique",
    "military_supremacy": "Suprematie militaire",
    "stability_first": "Stabilite prioritaire",
    "alliance_building": "Construction d'alliances",
    "nuclear_deterrence": "Dissuasion nucleaire",
    "defensive": "Posture defensive",
}

ACTION_TRANSLATIONS = {
    "ECONOMIE": "Developper l'economie",
    "MILITAIRE": "Renforcer l'armee",
    "TECHNOLOGIE": "Investir en R&D",
    "STABILITE": "Ameliorer la stabilite",
    "INFLUENCE": "Etendre l'influence",
    "SANCTIONS": "Imposer des sanctions",
    "ALLIANCE": "Former une alliance",
    "NUCLEAIRE": "Programme nucleaire",
    "RIEN": "Maintenir le statu quo",
}


@router.get("/player/advice/{country_id}", response_model=StrategicAdviceResponse)
async def get_strategic_advice(country_id: str, use_ollama: bool = True):
    """
    Get strategic advice for a player country.
    Uses StrategicAI to analyze situation and optionally Ollama for enhanced advice.
    """
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    settings = get_settings()
    ollama = get_ollama()
    strategic_ai = StrategicAI()

    # Get algorithmic analysis
    analysis = await strategic_ai.analyze_situation(country, world)

    # Format threats for response
    threats = []
    for threat_id, data in analysis["threats"].items():
        threat_country = world.get_country(threat_id) if threat_id != "global_instability" else None
        threats.append({
            "id": threat_id,
            "name_fr": threat_country.name_fr if threat_country else "Instabilite mondiale",
            "type": data.get("type", "unknown"),
            "level": data.get("level", "low"),
            "power_diff": data.get("power_diff", 0),
            "relation": data.get("relation"),
        })

    # Format opportunities for response
    opportunities = []
    for opp in analysis["opportunities"]:
        opp_data = {
            "type": opp["type"],
            "priority": opp.get("priority", "medium"),
        }
        if opp["type"] == "alliance":
            target = world.get_country(opp["target"])
            opp_data["target_id"] = opp["target"]
            opp_data["target_name_fr"] = target.name_fr if target else opp["target"]
            opp_data["relation"] = opp.get("relation", 0)
            opp_data["description_fr"] = f"Alliance possible avec {opp_data['target_name_fr']}"
        elif opp["type"] == "economic_growth":
            opp_data["potential"] = opp.get("potential", 0)
            opp_data["description_fr"] = "Potentiel de croissance economique"
        elif opp["type"] == "nuclear_program":
            opp_data["current"] = opp.get("current", 0)
            opp_data["description_fr"] = "Developpement nucleaire possible"
        elif opp["type"] == "influence_expansion":
            opp_data["soft_power"] = opp.get("current_soft_power", 0)
            opp_data["description_fr"] = "Extension d'influence mondiale"
        opportunities.append(opp_data)

    # Format recommendations
    recommendations = []
    for rec in analysis["recommended_actions"]:
        action = rec["action"]
        recommendations.append({
            "action": action,
            "action_fr": ACTION_TRANSLATIONS.get(action, action),
            "target": rec.get("target"),
            "target_name_fr": world.get_country(rec["target"]).name_fr if rec.get("target") and world.get_country(rec["target"]) else None,
            "priority": rec.get("priority", 1),
            "reason_fr": rec.get("reason", ""),
            "command": _build_command_suggestion(action, rec.get("target"), world),
        })

    # Build diplomatic summary
    power_analysis = analysis["power_analysis"]
    diplomatic_summary = {
        "allies_count": len(country.allies),
        "rivals_count": len(country.rivals),
        "at_war": len(country.at_war) > 0,
        "wars_count": len(country.at_war),
        "sanctions_active": len(country.sanctions_on),
        "blocs": country.blocs,
        "superpower_relations": power_analysis.get("superpower_relations", {}),
    }

    # Try to get Ollama advice if available and requested
    ollama_advice = None
    ollama_available = False

    if use_ollama and settings.ai_mode == "ollama":
        ollama_available = await ollama.check_connection()
        if ollama_available:
            try:
                decision = await strategic_ai.make_strategic_decision(country, world)
                if decision and decision.get("reason"):
                    ollama_advice = decision.get("reason", "")
                    if decision.get("risks"):
                        ollama_advice += f"\n\nRisques: {decision.get('risks')}"
            except Exception as e:
                logger.warning(f"Ollama advice failed: {e}")

    goal = analysis["strategic_goal"].value
    return StrategicAdviceResponse(
        country_id=country_id.upper(),
        strategic_goal=goal,
        strategic_goal_fr=GOAL_TRANSLATIONS.get(goal, goal),
        power_rank=power_analysis["country_rank"],
        total_countries=power_analysis["total_countries"],
        threats=threats,
        opportunities=opportunities,
        recommendations=recommendations,
        diplomatic_summary=diplomatic_summary,
        ollama_advice=ollama_advice,
        ollama_available=ollama_available,
    )


def _build_command_suggestion(action: str, target: Optional[str], world) -> str:
    """Build a natural language command suggestion"""
    target_name = ""
    if target:
        country = world.get_country(target)
        target_name = country.name_fr if country else target

    commands = {
        "ECONOMIE": "Lancer un programme de stimulation economique",
        "MILITAIRE": "Augmenter le budget de defense et moderniser l'armee",
        "TECHNOLOGIE": "Investir massivement en recherche et developpement",
        "STABILITE": "Lancer des reformes pour ameliorer la stabilite nationale",
        "INFLUENCE": "Etendre notre influence diplomatique et culturelle",
        "SANCTIONS": f"Imposer des sanctions economiques contre {target_name}" if target_name else "Imposer des sanctions",
        "ALLIANCE": f"Proposer une alliance strategique avec {target_name}" if target_name else "Former de nouvelles alliances",
        "NUCLEAIRE": "Accelerer le programme nucleaire",
        "RIEN": "Maintenir les politiques actuelles",
    }
    return commands.get(action, "")


@router.get("/player/geopolitical")
async def get_world_geopolitical_analysis():
    """Get comprehensive geopolitical analysis of the world"""
    world = get_world()
    return await get_geopolitical_analysis(world)


# ============================================================================
# DILEMMAS
# ============================================================================

from schemas.interaction import PendingDilemmasResponse, DilemmaResolveRequest, DilemmaResolveResponse
from engine.dilemma import dilemma_manager


@router.get("/dilemmas/{country_id}/pending", response_model=PendingDilemmasResponse)
async def get_pending_dilemmas(country_id: str):
    """Get all pending dilemmas for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    # Get pending dilemmas from the global dilemma manager
    pending = dilemma_manager.get_pending_dilemmas(country_id.upper())

    return PendingDilemmasResponse(
        country_id=country_id.upper(),
        pending_dilemmas=pending,
        count=len(pending)
    )


@router.post("/dilemmas/{dilemma_id}/resolve")
async def resolve_dilemma(dilemma_id: str, request: DilemmaResolveRequest):
    """Resolve a dilemma by choosing an option"""
    world = get_world()
    country = world.get_country(request.player_country_id.upper())

    if not country:
        raise HTTPException(status_code=404, detail=f"Country {request.player_country_id} not found")

    # Resolve the dilemma using the global dilemma manager
    result = dilemma_manager.resolve_dilemma(
        dilemma_id=dilemma_id,
        choice_index=request.choice_id,
        world=world
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"Dilemma {dilemma_id} not found or already resolved")

    return {
        "success": True,
        "dilemma_id": dilemma_id,
        "choice_id": request.choice_id,
        "message": f"Dilemma resolved with choice {request.choice_id}",
        "effects": result.get("effects", []),
        "relation_changes": result.get("relation_changes", {}),
        "events_triggered": result.get("events", [])
    }
