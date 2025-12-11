"""API routes for leaders management"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from engine.leaders import leader_manager

router = APIRouter(prefix="/leaders", tags=["leaders"])


@router.get("")
async def get_all_leaders() -> Dict[str, Any]:
    """Get all world leaders with their traits"""
    return {
        "leaders": leader_manager.get_all_leaders()
    }


@router.get("/{country_id}")
async def get_leader(country_id: str) -> Dict[str, Any]:
    """Get leader for a specific country"""
    leader = leader_manager.get_leader_dict(country_id)
    if not leader:
        raise HTTPException(status_code=404, detail=f"No leader found for {country_id}")
    return {"leader": leader}


@router.get("/{country_id}/traits")
async def get_leader_traits(country_id: str) -> Dict[str, Any]:
    """Get combined effects of leader's traits"""
    leader = leader_manager.get_leader(country_id)
    if not leader:
        raise HTTPException(status_code=404, detail=f"No leader found for {country_id}")

    return {
        "country_id": country_id,
        "leader_name": leader.name,
        "traits": leader.traits,
        "combined_effects": leader_manager.get_leader_traits_effects(country_id)
    }


@router.get("/{country_id}/reaction/{event_type}")
async def get_leader_reaction(country_id: str, event_type: str) -> Dict[str, Any]:
    """Get a contextual reaction from a leader based on an event type"""
    leader = leader_manager.get_leader(country_id)
    if not leader:
        raise HTTPException(status_code=404, detail=f"No leader found for {country_id}")

    reaction = leader_manager.get_leader_reaction(country_id, event_type)
    return {
        "country_id": country_id,
        "leader_name": leader.name,
        "event_type": event_type,
        "reaction": reaction
    }
