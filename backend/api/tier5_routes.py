"""Tier 5 countries routes for Historia Lite"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from schemas.game import Tier5CountryResponse, Tier5SummaryResponse
from api.game_state import get_world

router = APIRouter(prefix="/api", tags=["tier5"])


@router.get("/tier5", response_model=list[Tier5CountryResponse])
async def get_tier5_countries(
    region: Optional[str] = None,
    alignment: Optional[str] = None,
    protector: Optional[str] = None,
    in_crisis: Optional[bool] = None
):
    """Get all Tier 5 countries with optional filters"""
    world = get_world()
    countries = list(world.tier5_countries.values())

    if region:
        countries = [c for c in countries if c.region == region.lower()]

    if alignment:
        countries = [c for c in countries if c.get_alignment_label() == alignment.lower()]

    if protector:
        countries = [c for c in countries if c.protector == protector.upper()]

    if in_crisis is not None:
        countries = [c for c in countries if c.in_crisis == in_crisis]

    return [Tier5CountryResponse.from_tier5_country(c) for c in countries]


@router.get("/tier5/summary", response_model=Tier5SummaryResponse)
async def get_tier5_summary():
    """Get summary statistics for Tier 5 countries"""
    world = get_world()
    countries = list(world.tier5_countries.values())

    by_region = {}
    for c in countries:
        by_region[c.region] = by_region.get(c.region, 0) + 1

    by_alignment = {}
    for c in countries:
        label = c.get_alignment_label()
        by_alignment[label] = by_alignment.get(label, 0) + 1

    by_protector = {}
    for c in countries:
        if c.protector:
            by_protector[c.protector] = by_protector.get(c.protector, 0) + 1

    in_crisis_count = len([c for c in countries if c.in_crisis])

    pro_west = len([c for c in countries if c.alignment < -30])
    pro_east = len([c for c in countries if c.alignment > 30])
    neutral = len(countries) - pro_west - pro_east

    return Tier5SummaryResponse(
        total=len(countries),
        by_region=by_region,
        by_alignment=by_alignment,
        by_protector=by_protector,
        in_crisis=in_crisis_count,
        pro_west=pro_west,
        pro_east=pro_east,
        neutral=neutral
    )


@router.get("/tier5/{country_id}", response_model=Tier5CountryResponse)
async def get_tier5_country(country_id: str):
    """Get details of a specific Tier 5 country"""
    world = get_world()
    country = world.get_tier5_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Tier 5 country {country_id} not found")
    return Tier5CountryResponse.from_tier5_country(country)


@router.get("/tier5/region/{region}", response_model=list[Tier5CountryResponse])
async def get_tier5_by_region(region: str):
    """Get all Tier 5 countries in a specific region"""
    world = get_world()
    countries = world.get_tier5_by_region(region.lower())
    if not countries:
        raise HTTPException(status_code=404, detail=f"No Tier 5 countries in region {region}")
    return [Tier5CountryResponse.from_tier5_country(c) for c in countries]


@router.get("/tier5/protector/{protector_id}", response_model=list[Tier5CountryResponse])
async def get_tier5_by_protector(protector_id: str):
    """Get all Tier 5 countries protected by a specific power"""
    world = get_world()
    countries = world.get_tier5_by_protector(protector_id.upper())
    return [Tier5CountryResponse.from_tier5_country(c) for c in countries]
