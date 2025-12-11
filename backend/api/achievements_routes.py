"""API routes for achievements"""
from fastapi import APIRouter
from typing import Dict, Any, List
from engine.achievements import achievement_manager

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("")
async def get_all_achievements() -> Dict[str, Any]:
    """Get all achievements with progress"""
    return {
        "achievements": achievement_manager.get_all_achievements(),
        "summary": achievement_manager.get_summary()
    }


@router.get("/unlocked")
async def get_unlocked_achievements() -> Dict[str, Any]:
    """Get only unlocked achievements"""
    return {
        "achievements": achievement_manager.get_unlocked_achievements(),
        "total_points": achievement_manager.get_total_points()
    }


@router.get("/summary")
async def get_achievements_summary() -> Dict[str, Any]:
    """Get achievement summary stats"""
    return achievement_manager.get_summary()


@router.get("/categories")
async def get_achievement_categories() -> Dict[str, Any]:
    """Get achievement categories"""
    return {
        "categories": achievement_manager.categories,
        "rarities": achievement_manager.rarities
    }


@router.post("/check")
async def check_achievements() -> Dict[str, Any]:
    """Manually trigger achievement check (normally done automatically)"""
    from engine.world import world_state
    if world_state:
        newly_unlocked = achievement_manager.check_achievements(world_state)
        return {
            "checked": True,
            "newly_unlocked": newly_unlocked,
            "total_unlocked": len(achievement_manager.unlocked_ids)
        }
    return {
        "checked": False,
        "error": "No active world state"
    }
