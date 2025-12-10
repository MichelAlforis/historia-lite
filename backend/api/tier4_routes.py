"""Tier 4 countries routes for Historia Lite"""
from typing import Optional
from fastapi import APIRouter, HTTPException

from schemas.game import Tier4CountryResponse, Tier4SummaryResponse
from api.game_state import get_world

router = APIRouter(prefix="/api", tags=["tier4"])


@router.get("/tier4", response_model=list[Tier4CountryResponse])
async def get_tier4_countries(
    region: Optional[str] = None,
    alignment: Optional[str] = None,
    in_crisis: Optional[bool] = None
):
    """Get all Tier 4 countries with optional filters"""
    world = get_world()
    countries = list(world.tier4_countries.values())

    if region:
        countries = [c for c in countries if c.region == region.lower()]

    if alignment:
        countries = [c for c in countries if c.get_alignment_label() == alignment.lower()]

    if in_crisis is not None:
        countries = [c for c in countries if c.in_crisis == in_crisis]

    return [Tier4CountryResponse.from_tier4_country(c) for c in countries]


@router.get("/tier4/summary", response_model=Tier4SummaryResponse)
async def get_tier4_summary():
    """Get summary statistics for Tier 4 countries"""
    world = get_world()
    countries = list(world.tier4_countries.values())

    by_region = {}
    for c in countries:
        by_region[c.region] = by_region.get(c.region, 0) + 1

    by_alignment = {}
    for c in countries:
        label = c.get_alignment_label()
        by_alignment[label] = by_alignment.get(label, 0) + 1

    in_crisis_count = len([c for c in countries if c.in_crisis])

    pro_west = len([c for c in countries if c.alignment < -30])
    pro_east = len([c for c in countries if c.alignment > 30])
    neutral = len(countries) - pro_west - pro_east

    return Tier4SummaryResponse(
        total=len(countries),
        by_region=by_region,
        by_alignment=by_alignment,
        in_crisis=in_crisis_count,
        pro_west=pro_west,
        pro_east=pro_east,
        neutral=neutral
    )


@router.get("/tier4/{country_id}", response_model=Tier4CountryResponse)
async def get_tier4_country(country_id: str):
    """Get details of a specific Tier 4 country"""
    world = get_world()
    country = world.get_tier4_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Tier 4 country {country_id} not found")
    return Tier4CountryResponse.from_tier4_country(country)


@router.get("/tier4/region/{region}", response_model=list[Tier4CountryResponse])
async def get_tier4_by_region(region: str):
    """Get all Tier 4 countries in a specific region"""
    world = get_world()
    countries = world.get_tier4_by_region(region.lower())
    if not countries:
        raise HTTPException(status_code=404, detail=f"No Tier 4 countries in region {region}")
    return [Tier4CountryResponse.from_tier4_country(c) for c in countries]
