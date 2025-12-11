"""Tier 6 countries routes for Historia Lite"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from schemas.game import Tier6CountryResponse, Tier6SummaryResponse
from api.game_state import get_world
from ai.decision_tier6 import get_protector_influence

router = APIRouter(prefix="/api", tags=["tier6"])


@router.get("/tier6", response_model=list[Tier6CountryResponse])
async def get_tier6_countries(
    region: Optional[str] = None,
    protector: Optional[str] = None,
    is_territory: Optional[bool] = None,
    special_status: Optional[str] = None
):
    """Get all Tier 6 countries with optional filters"""
    world = get_world()
    countries = list(world.tier6_countries.values())

    if region:
        countries = [c for c in countries if c.region == region.lower()]

    if protector:
        countries = [c for c in countries if c.protector == protector.upper()]

    if is_territory is not None:
        countries = [c for c in countries if c.is_territory == is_territory]

    if special_status:
        countries = [c for c in countries if c.special_status == special_status.lower()]

    return [Tier6CountryResponse.from_tier6_country(c) for c in countries]


@router.get("/tier6/summary", response_model=Tier6SummaryResponse)
async def get_tier6_summary():
    """Get summary statistics for Tier 6 countries"""
    world = get_world()
    countries = list(world.tier6_countries.values())

    by_region = {}
    for c in countries:
        by_region[c.region] = by_region.get(c.region, 0) + 1

    by_protector = {}
    for c in countries:
        if c.protector:
            by_protector[c.protector] = by_protector.get(c.protector, 0) + 1

    by_status = {}
    for c in countries:
        if c.special_status:
            by_status[c.special_status] = by_status.get(c.special_status, 0) + 1

    territories = len([c for c in countries if c.is_territory])
    sovereign = len(countries) - territories

    return Tier6SummaryResponse(
        total=len(countries),
        by_region=by_region,
        by_protector=by_protector,
        by_special_status=by_status,
        territories=territories,
        sovereign=sovereign
    )


@router.get("/tier6/{country_id}", response_model=Tier6CountryResponse)
async def get_tier6_country(country_id: str):
    """Get details of a specific Tier 6 country"""
    world = get_world()
    country = world.get_tier6_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Tier 6 country {country_id} not found")
    return Tier6CountryResponse.from_tier6_country(country)


@router.get("/tier6/{country_id}/influence")
async def get_tier6_influence(country_id: str):
    """Get influence information for a Tier 6 country based on its protector"""
    world = get_world()
    country = world.get_tier6_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Tier 6 country {country_id} not found")
    return get_protector_influence(country, world)


@router.get("/tier6/region/{region}", response_model=list[Tier6CountryResponse])
async def get_tier6_by_region(region: str):
    """Get all Tier 6 countries in a specific region"""
    world = get_world()
    countries = world.get_tier6_by_region(region.lower())
    if not countries:
        raise HTTPException(status_code=404, detail=f"No Tier 6 countries in region {region}")
    return [Tier6CountryResponse.from_tier6_country(c) for c in countries]


@router.get("/tier6/protector/{protector_id}", response_model=list[Tier6CountryResponse])
async def get_tier6_by_protector(protector_id: str):
    """Get all Tier 6 countries protected by a specific power"""
    world = get_world()
    countries = world.get_tier6_by_protector(protector_id.upper())
    return [Tier6CountryResponse.from_tier6_country(c) for c in countries]
