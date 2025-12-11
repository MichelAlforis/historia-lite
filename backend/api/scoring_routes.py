"""Scoring API routes with Fog of War support"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from engine.scoring import scoring_manager, CountryScores
from engine.espionage import espionage_manager
from api.game_state import game_state

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


@router.get("/country/{country_id}")
async def get_country_scores(
    country_id: str,
    observer: Optional[str] = Query(None, description="Observer country ID for fog of war")
) -> CountryScores:
    """
    Get detailed scores for a country.

    If observer is specified, applies fog of war based on intel quality.
    Military and nuclear info may be hidden or approximated.
    """
    if not game_state.world:
        raise HTTPException(status_code=503, detail="World not initialized")

    country = game_state.world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    return scoring_manager.calculate_country_scores(
        country,
        game_state.world,
        observer_id=observer
    )


@router.get("/rankings")
async def get_rankings(
    observer: Optional[str] = Query(None, description="Observer country ID for fog of war")
):
    """
    Get country rankings.

    If observer is specified, scores may be approximate for countries
    with poor intel coverage.
    """
    if not game_state.world:
        raise HTTPException(status_code=503, detail="World not initialized")

    return scoring_manager.get_rankings(game_state.world, observer_id=observer)


@router.get("/intel/{observer_id}/{target_id}")
async def get_intel_quality(observer_id: str, target_id: str):
    """
    Get intelligence quality between two countries.

    Returns:
    - intel_score: 0-100 numeric score
    - intel_quality: none/partial/good/very_good/excellent/perfect
    - visible_categories: which score categories are visible
    """
    if not game_state.world:
        raise HTTPException(status_code=503, detail="World not initialized")

    observer = game_state.world.get_country(observer_id)
    target = game_state.world.get_country(target_id)

    if not observer:
        raise HTTPException(status_code=404, detail=f"Observer {observer_id} not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Target {target_id} not found")

    intel_score = espionage_manager.get_intel_score(observer, target, game_state.world)
    intel_quality = espionage_manager.get_intel_quality(intel_score)

    # Determine visible categories
    thresholds = {
        "economic": 20,
        "stability": 40,
        "influence": 40,
        "resources": 40,
        "leadership": 40,
        "military": 60,
        "intelligence": 80,
        "nuclear": 80,
    }

    visible = {cat: intel_score >= thresh for cat, thresh in thresholds.items()}

    return {
        "observer_id": observer_id,
        "target_id": target_id,
        "intel_score": intel_score,
        "intel_quality": intel_quality.value,
        "visible_categories": visible,
        "nuclear_info": espionage_manager.get_nuclear_display(target, intel_score)
    }


@router.get("/compare/{country_a}/{country_b}")
async def compare_countries(
    country_a: str,
    country_b: str,
    observer: Optional[str] = Query(None, description="Observer country ID")
):
    """
    Compare scores between two countries.

    Returns side-by-side comparison with fog of war applied if observer specified.
    """
    if not game_state.world:
        raise HTTPException(status_code=503, detail="World not initialized")

    ca = game_state.world.get_country(country_a)
    cb = game_state.world.get_country(country_b)

    if not ca:
        raise HTTPException(status_code=404, detail=f"Country {country_a} not found")
    if not cb:
        raise HTTPException(status_code=404, detail=f"Country {country_b} not found")

    scores_a = scoring_manager.calculate_country_scores(ca, game_state.world, observer)
    scores_b = scoring_manager.calculate_country_scores(cb, game_state.world, observer)

    return {
        "country_a": scores_a,
        "country_b": scores_b,
        "comparison": {
            "military": scores_a.military.score - scores_b.military.score,
            "economic": scores_a.economic.score - scores_b.economic.score,
            "stability": scores_a.stability.score - scores_b.stability.score,
            "influence": scores_a.influence.score - scores_b.influence.score,
            "global": scores_a.global_score - scores_b.global_score,
        }
    }
