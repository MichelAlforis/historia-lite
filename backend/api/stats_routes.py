"""API routes for historical stats"""
from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
from engine.stats_history import stats_history

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/history/{country_id}")
async def get_country_history(
    country_id: str,
    limit: Optional[int] = Query(None, ge=1, le=60, description="Max records to return")
) -> Dict[str, Any]:
    """Get historical stats for a specific country"""
    history = stats_history.get_country_history(country_id, limit)
    return {
        "country_id": country_id,
        "history": history,
        "count": len(history)
    }


@router.get("/history/{country_id}/combined")
async def get_combined_history(
    country_id: str,
    limit: Optional[int] = Query(None, ge=1, le=60, description="Max records to return")
) -> Dict[str, Any]:
    """Get combined country + world stats history (useful for charts)"""
    history = stats_history.get_combined_history(country_id, limit)
    return {
        "country_id": country_id,
        "history": history,
        "count": len(history)
    }


@router.get("/world")
async def get_world_history(
    limit: Optional[int] = Query(None, ge=1, le=60, description="Max records to return")
) -> Dict[str, Any]:
    """Get historical world stats"""
    history = stats_history.get_world_history(limit)
    return {
        "history": history,
        "count": len(history)
    }


@router.get("/compare")
async def compare_countries(
    countries: str = Query(..., description="Comma-separated list of country IDs"),
    metric: str = Query("economy", description="Metric to compare"),
    limit: Optional[int] = Query(12, ge=1, le=60)
) -> Dict[str, Any]:
    """Compare a specific metric across multiple countries"""
    country_ids = [c.strip() for c in countries.split(',')]

    result = {
        "metric": metric,
        "countries": {},
        "dates": []
    }

    # Get history for each country
    for country_id in country_ids:
        history = stats_history.get_country_history(country_id, limit)
        if history:
            result["countries"][country_id] = [
                h.get(metric, 0) for h in history
            ]
            # Use first country's dates as reference
            if not result["dates"]:
                result["dates"] = [h.get("date", "") for h in history]

    return result
