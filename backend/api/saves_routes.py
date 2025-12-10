"""Save/Load game management routes for Historia Lite"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException

from api.game_state import get_world, get_settings, update_settings
from engine.world import World, load_world_from_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/saves", tags=["saves"])

# Directory for save files
SAVES_DIR = Path(__file__).parent.parent / "saves"
SAVES_DIR.mkdir(exist_ok=True)


class SaveMetadata(BaseModel):
    """Metadata for a save file"""
    id: str
    name: str
    created_at: str
    year: int
    player_country: Optional[str] = None
    countries_count: int
    global_tension: int
    description: Optional[str] = None


class SaveGameRequest(BaseModel):
    """Request to save the current game"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class SaveGameResponse(BaseModel):
    """Response after saving game"""
    success: bool
    message: str
    save_id: str
    metadata: SaveMetadata


class LoadGameResponse(BaseModel):
    """Response after loading game"""
    success: bool
    message: str
    year: int
    countries_count: int


class SavesList(BaseModel):
    """List of available saves"""
    saves: List[SaveMetadata]
    total: int


class ExportGameResponse(BaseModel):
    """Response with full game state for export"""
    metadata: SaveMetadata
    world_state: dict
    settings: dict


# ==================== Routes ====================


@router.get("/list", response_model=SavesList)
async def list_saves():
    """List all available save files"""
    try:
        saves: List[SaveMetadata] = []

        # Read all save files
        for save_file in SAVES_DIR.glob("*.json"):
            if save_file.name.startswith("_"):
                continue

            try:
                with open(save_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    metadata = data.get("metadata", {})
                    saves.append(SaveMetadata(
                        id=save_file.stem,
                        name=metadata.get("name", save_file.stem),
                        created_at=metadata.get("created_at", "Unknown"),
                        year=metadata.get("year", 2025),
                        player_country=metadata.get("player_country"),
                        countries_count=metadata.get("countries_count", 0),
                        global_tension=metadata.get("global_tension", 50),
                        description=metadata.get("description"),
                    ))
            except Exception as e:
                logger.warning(f"Could not read save file {save_file}: {e}")

        # Sort by creation date (newest first)
        saves.sort(key=lambda s: s.created_at, reverse=True)

        return SavesList(saves=saves, total=len(saves))

    except Exception as e:
        logger.error(f"Error listing saves: {e}")
        raise HTTPException(status_code=500, detail="Could not list saves")


@router.post("/save", response_model=SaveGameResponse)
async def save_game(request: SaveGameRequest):
    """Save the current game state"""
    try:
        world = get_world()
        settings = get_settings()

        # Generate save ID from timestamp
        timestamp = datetime.now()
        save_id = timestamp.strftime("%Y%m%d_%H%M%S")

        # Get player country if set
        player_country = None
        try:
            from api.player_routes import get_player_country_id
            player_country = get_player_country_id()
        except Exception:
            pass

        # Create metadata
        metadata = SaveMetadata(
            id=save_id,
            name=request.name,
            created_at=timestamp.isoformat(),
            year=world.year,
            player_country=player_country,
            countries_count=len(world.countries),
            global_tension=world.global_tension,
            description=request.description,
        )

        # Serialize world state
        world_state = world.model_dump()

        # Create save data
        save_data = {
            "metadata": metadata.model_dump(),
            "settings": settings.model_dump(),
            "world_state": world_state,
            "player_country": player_country,
        }

        # Write to file
        save_path = SAVES_DIR / f"{save_id}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Game saved: {save_id} - {request.name}")

        return SaveGameResponse(
            success=True,
            message=f"Partie sauvegardee: {request.name}",
            save_id=save_id,
            metadata=metadata,
        )

    except Exception as e:
        logger.error(f"Error saving game: {e}")
        raise HTTPException(status_code=500, detail=f"Could not save game: {str(e)}")


@router.post("/load/{save_id}", response_model=LoadGameResponse)
async def load_game(save_id: str):
    """Load a saved game"""
    try:
        save_path = SAVES_DIR / f"{save_id}.json"

        if not save_path.exists():
            raise HTTPException(status_code=404, detail=f"Save not found: {save_id}")

        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)

        # Load world state
        world_state = save_data.get("world_state", {})

        # Reconstruct world from saved state
        from api.game_state import _world, _event_pool
        import api.game_state as game_state

        # Create new world from saved data
        game_state._world = World(**world_state)

        # Restore settings
        saved_settings = save_data.get("settings", {})
        if saved_settings:
            update_settings(
                ai_mode=saved_settings.get("ai_mode"),
                ollama_url=saved_settings.get("ollama_url"),
                ollama_model=saved_settings.get("ollama_model"),
            )

        # Restore player country
        player_country = save_data.get("player_country")
        if player_country:
            try:
                from api.player_routes import set_player_country_id
                set_player_country_id(player_country)
            except Exception:
                pass

        world = get_world()
        logger.info(f"Game loaded: {save_id}")

        return LoadGameResponse(
            success=True,
            message=f"Partie chargee: Annee {world.year}",
            year=world.year,
            countries_count=len(world.countries),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading game: {e}")
        raise HTTPException(status_code=500, detail=f"Could not load game: {str(e)}")


@router.delete("/{save_id}")
async def delete_save(save_id: str):
    """Delete a save file"""
    try:
        save_path = SAVES_DIR / f"{save_id}.json"

        if not save_path.exists():
            raise HTTPException(status_code=404, detail=f"Save not found: {save_id}")

        save_path.unlink()
        logger.info(f"Save deleted: {save_id}")

        return {"success": True, "message": f"Sauvegarde supprimee: {save_id}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting save: {e}")
        raise HTTPException(status_code=500, detail=f"Could not delete save: {str(e)}")


@router.get("/{save_id}", response_model=SaveMetadata)
async def get_save_metadata(save_id: str):
    """Get metadata for a specific save"""
    try:
        save_path = SAVES_DIR / f"{save_id}.json"

        if not save_path.exists():
            raise HTTPException(status_code=404, detail=f"Save not found: {save_id}")

        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)

        metadata = save_data.get("metadata", {})
        return SaveMetadata(
            id=save_id,
            name=metadata.get("name", save_id),
            created_at=metadata.get("created_at", "Unknown"),
            year=metadata.get("year", 2025),
            player_country=metadata.get("player_country"),
            countries_count=metadata.get("countries_count", 0),
            global_tension=metadata.get("global_tension", 50),
            description=metadata.get("description"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting save metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Could not get save metadata: {str(e)}")


@router.get("/{save_id}/export", response_model=ExportGameResponse)
async def export_save(save_id: str):
    """Export a save as JSON (for download/sharing)"""
    try:
        save_path = SAVES_DIR / f"{save_id}.json"

        if not save_path.exists():
            raise HTTPException(status_code=404, detail=f"Save not found: {save_id}")

        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)

        metadata = save_data.get("metadata", {})

        return ExportGameResponse(
            metadata=SaveMetadata(
                id=save_id,
                name=metadata.get("name", save_id),
                created_at=metadata.get("created_at", "Unknown"),
                year=metadata.get("year", 2025),
                player_country=metadata.get("player_country"),
                countries_count=metadata.get("countries_count", 0),
                global_tension=metadata.get("global_tension", 50),
                description=metadata.get("description"),
            ),
            world_state=save_data.get("world_state", {}),
            settings=save_data.get("settings", {}),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting save: {e}")
        raise HTTPException(status_code=500, detail=f"Could not export save: {str(e)}")


@router.post("/import")
async def import_save(save_data: dict):
    """Import a save from JSON data"""
    try:
        # Validate required fields
        if "world_state" not in save_data:
            raise HTTPException(status_code=400, detail="Missing world_state in import data")

        # Generate new save ID
        timestamp = datetime.now()
        save_id = f"import_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # Get or create metadata
        metadata = save_data.get("metadata", {})
        metadata["id"] = save_id
        metadata["created_at"] = timestamp.isoformat()
        if "name" not in metadata:
            metadata["name"] = f"Import {timestamp.strftime('%Y-%m-%d %H:%M')}"

        # Get world info for metadata
        world_state = save_data["world_state"]
        metadata["year"] = world_state.get("year", 2025)
        metadata["countries_count"] = len(world_state.get("countries", {}))
        metadata["global_tension"] = world_state.get("global_tension", 50)

        # Create save data
        save_to_write = {
            "metadata": metadata,
            "settings": save_data.get("settings", {}),
            "world_state": world_state,
            "player_country": save_data.get("player_country"),
        }

        # Write to file
        save_path = SAVES_DIR / f"{save_id}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_to_write, f, ensure_ascii=False, indent=2)

        logger.info(f"Save imported: {save_id}")

        return {
            "success": True,
            "message": f"Sauvegarde importee: {metadata.get('name', save_id)}",
            "save_id": save_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing save: {e}")
        raise HTTPException(status_code=500, detail=f"Could not import save: {str(e)}")


@router.post("/autosave")
async def create_autosave():
    """Create an autosave (replaces previous autosave)"""
    try:
        world = get_world()
        settings = get_settings()

        # Get player country if set
        player_country = None
        try:
            from api.player_routes import get_player_country_id
            player_country = get_player_country_id()
        except Exception:
            pass

        timestamp = datetime.now()

        # Create metadata
        metadata = {
            "id": "autosave",
            "name": f"Autosave - Annee {world.year}",
            "created_at": timestamp.isoformat(),
            "year": world.year,
            "player_country": player_country,
            "countries_count": len(world.countries),
            "global_tension": world.global_tension,
            "description": "Sauvegarde automatique",
        }

        # Create save data
        save_data = {
            "metadata": metadata,
            "settings": settings.model_dump(),
            "world_state": world.model_dump(),
            "player_country": player_country,
        }

        # Write to file (overwrite previous autosave)
        save_path = SAVES_DIR / "autosave.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Autosave created: Year {world.year}")

        return {
            "success": True,
            "message": f"Sauvegarde automatique: Annee {world.year}",
        }

    except Exception as e:
        logger.error(f"Error creating autosave: {e}")
        raise HTTPException(status_code=500, detail=f"Could not create autosave: {str(e)}")
