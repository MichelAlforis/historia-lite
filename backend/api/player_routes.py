"""Player and command routes for Historia Lite"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from schemas.interaction import (
    CommandRequest,
    CommandResponse,
    CommandConfirmRequest,
)
from ai.command_interpreter import CommandInterpreter
from api.game_state import get_world, get_ollama, get_settings

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
    response = await interpreter.confirm_and_execute(
        command_id=request.command_id,
        country=country,
        world=world
    )

    if not response:
        raise HTTPException(
            status_code=404,
            detail=f"Command {request.command_id} not found or already executed"
        )

    return response
