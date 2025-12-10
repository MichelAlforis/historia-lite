"""Influence zones and geopolitical influence API routes"""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.influence import (
    influence_manager,
    military_base_manager,
    InfluenceType,
    MilitaryBase,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/influence", tags=["influence"])


# ==================== Request/Response Models ====================

class EstablishBaseRequest(BaseModel):
    owner_id: str
    host_country_id: str
    zone_id: str
    base_type: str  # air_base, naval_base, army_base, drone_base, listening_post
    personnel: int = 1000
    base_name: Optional[str] = None


class CloseBaseRequest(BaseModel):
    base_id: str


class CulturalProgramRequest(BaseModel):
    power_id: str
    zone_id: str
    program_type: str  # language_institute, media, education, cultural_center
    investment: int = 10  # 1-100


class ArmsDealRequest(BaseModel):
    seller_id: str
    buyer_id: str
    value: int = 50  # 1-100


class ReligiousMissionRequest(BaseModel):
    power_id: str
    zone_id: str
    mission_type: str  # missionary, charity, education
    investment: int = 10


# ==================== Zone Information Endpoints ====================

@router.get("/zones")
async def list_influence_zones():
    """List all influence zones with current status"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    zones = []
    for zone in world.influence_zones.values():
        zones.append({
            "id": zone.id,
            "name": zone.name,
            "name_fr": zone.name_fr,
            "dominant_power": zone.dominant_power,
            "contested_by": zone.contested_by,
            "is_contested": zone.is_contested(),
            "influence_type": zone.influence_type,
            "strength": zone.strength,
            "influence_levels": zone.influence_levels,
            "countries_in_zone": zone.countries_in_zone,
            # Cultural factors
            "dominant_religion": zone.dominant_religion,
            "dominant_culture": zone.dominant_culture,
            "dominant_language": zone.dominant_language,
            # Resources
            "has_oil": zone.has_oil,
            "has_strategic_resources": zone.has_strategic_resources,
            "former_colonial_power": zone.former_colonial_power,
        })

    return {"zones": zones, "total": len(zones)}


@router.get("/zone/{zone_id}")
async def get_zone_details(zone_id: str):
    """Get detailed information about an influence zone"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    zone = world.influence_zones.get(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")

    return {
        "zone": {
            "id": zone.id,
            "name": zone.name,
            "name_fr": zone.name_fr,
            "dominant_power": zone.dominant_power,
            "contested_by": zone.contested_by,
            "countries_in_zone": zone.countries_in_zone,
            "influence_type": zone.influence_type,
            "strength": zone.strength,
            "dominant_religion": zone.dominant_religion,
            "dominant_culture": zone.dominant_culture,
            "dominant_language": zone.dominant_language,
            "has_oil": zone.has_oil,
            "has_strategic_resources": zone.has_strategic_resources,
            "former_colonial_power": zone.former_colonial_power,
        },
        "influence_levels": zone.influence_levels,
        "influence_breakdown": zone.influence_breakdown,
    }


@router.get("/zone/{zone_id}/breakdown")
async def get_zone_breakdown(zone_id: str):
    """Get detailed influence breakdown by type for each power"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    breakdown = influence_manager.get_zone_breakdown(zone_id, world)
    if "error" in breakdown:
        raise HTTPException(status_code=404, detail=breakdown["error"])

    return breakdown


# ==================== Military Base Endpoints ====================

@router.get("/military-bases")
async def list_military_bases():
    """List all military bases worldwide"""
    bases = military_base_manager.bases

    return {
        "bases": [
            {
                "id": b.id,
                "name": b.name,
                "name_fr": b.name_fr,
                "owner": b.owner,
                "host_country": b.host_country,
                "zone": b.zone,
                "type": b.type,
                "personnel": b.personnel,
                "strategic_value": b.strategic_value,
            }
            for b in bases.values()
        ],
        "total": len(bases),
    }


@router.get("/military-bases/owner/{country_id}")
async def get_bases_by_owner(country_id: str):
    """Get all military bases owned by a country"""
    bases = military_base_manager.get_bases_by_owner(country_id)

    return {
        "owner": country_id,
        "bases": [
            {
                "id": b.id,
                "name": b.name,
                "host_country": b.host_country,
                "zone": b.zone,
                "type": b.type,
                "personnel": b.personnel,
                "strategic_value": b.strategic_value,
            }
            for b in bases
        ],
        "total": len(bases),
        "total_personnel": sum(b.personnel for b in bases),
    }


@router.get("/military-bases/zone/{zone_id}")
async def get_bases_in_zone(zone_id: str):
    """Get all military bases in a zone"""
    bases = military_base_manager.get_bases_in_zone(zone_id)

    # Group by owner
    by_owner = {}
    for base in bases:
        if base.owner not in by_owner:
            by_owner[base.owner] = []
        by_owner[base.owner].append({
            "id": base.id,
            "name": base.name,
            "type": base.type,
            "personnel": base.personnel,
            "strategic_value": base.strategic_value,
        })

    return {
        "zone_id": zone_id,
        "bases": [b.__dict__ for b in bases],
        "by_owner": by_owner,
        "total": len(bases),
        "military_presence": {
            owner: military_base_manager.calculate_military_presence(zone_id, owner)
            for owner in by_owner.keys()
        },
    }


@router.post("/military-base/establish")
async def establish_military_base(request: EstablishBaseRequest):
    """Establish a new military base"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    success, message, effects = influence_manager.establish_base(
        owner_id=request.owner_id,
        host_country_id=request.host_country_id,
        zone_id=request.zone_id,
        base_type=request.base_type,
        personnel=request.personnel,
        world=world,
        base_name=request.base_name,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


@router.post("/military-base/close")
async def close_military_base(request: CloseBaseRequest):
    """Close a military base"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    success, message, effects = influence_manager.close_base(
        request.base_id, world
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


# ==================== Cultural/Religious Influence Endpoints ====================

@router.post("/cultural-program")
async def launch_cultural_program(request: CulturalProgramRequest):
    """Launch a cultural influence program (Confucius Institute, Alliance Francaise, etc.)"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    power = world.get_country(request.power_id)
    if not power:
        raise HTTPException(status_code=404, detail=f"Power {request.power_id} not found")

    zone = world.influence_zones.get(request.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {request.zone_id} not found")

    # Calculate bonus based on program type and investment
    base_bonus = request.investment // 10

    program_multipliers = {
        "language_institute": 1.5,  # Alliance Francaise, Confucius Institute
        "media": 1.2,  # Broadcasting (BBC, RT, CGTN)
        "education": 1.3,  # University programs, scholarships
        "cultural_center": 1.0,  # General cultural presence
    }

    multiplier = program_multipliers.get(request.program_type, 1.0)
    cultural_bonus = int(base_bonus * multiplier)

    # Update power's soft power
    old_soft = power.soft_power
    power.soft_power = min(100, power.soft_power + cultural_bonus // 2)

    program_names = {
        "language_institute": "Institut linguistique",
        "media": "Reseau mediatique",
        "education": "Programme educatif",
        "cultural_center": "Centre culturel",
    }

    return {
        "success": True,
        "message_fr": f"{program_names.get(request.program_type, 'Programme')} lance en {zone.name_fr}",
        "effects": {
            "cultural_influence_boost": cultural_bonus,
            "soft_power_change": power.soft_power - old_soft,
            "zone": zone.id,
            "investment": request.investment,
        },
    }


@router.post("/religious-mission")
async def launch_religious_mission(request: ReligiousMissionRequest):
    """Launch a religious influence mission"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    power = world.get_country(request.power_id)
    if not power:
        raise HTTPException(status_code=404, detail=f"Power {request.power_id} not found")

    zone = world.influence_zones.get(request.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {request.zone_id} not found")

    # Check religious compatibility
    power_religion = getattr(power, 'religion', None)
    zone_religion = zone.dominant_religion

    base_bonus = request.investment // 10

    # Same religion = higher bonus
    if power_religion and zone_religion and power_religion == zone_religion:
        religious_bonus = int(base_bonus * 1.5)
        compatibility = "compatible"
    else:
        religious_bonus = base_bonus // 2
        compatibility = "faible"

    mission_names = {
        "missionary": "Mission religieuse",
        "charity": "Oeuvre caritative",
        "education": "Ecoles religieuses",
    }

    return {
        "success": True,
        "message_fr": f"{mission_names.get(request.mission_type, 'Mission')} lancee en {zone.name_fr}",
        "effects": {
            "religious_influence_boost": religious_bonus,
            "compatibility": compatibility,
            "zone": zone.id,
            "investment": request.investment,
        },
    }


@router.post("/arms-deal")
async def sign_arms_deal(request: ArmsDealRequest):
    """Sign an arms deal to increase military influence"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    seller = world.get_country(request.seller_id)
    buyer = world.get_country(request.buyer_id)

    if not seller:
        raise HTTPException(status_code=404, detail=f"Seller {request.seller_id} not found")
    if not buyer:
        raise HTTPException(status_code=404, detail=f"Buyer {request.buyer_id} not found")

    # Economic effects
    seller_economy_boost = request.value // 20
    buyer_military_boost = request.value // 10

    old_seller_eco = seller.economy
    old_buyer_mil = buyer.military

    seller.economy = min(100, seller.economy + seller_economy_boost)
    buyer.military = min(100, buyer.military + buyer_military_boost)

    # Relation improvement
    seller.modify_relation(buyer.id, 10)
    buyer.modify_relation(seller.id, 10)

    # Mark dependency for influence calculation
    if not hasattr(buyer, 'arms_suppliers'):
        buyer.arms_suppliers = []
    if request.seller_id not in buyer.arms_suppliers:
        buyer.arms_suppliers.append(request.seller_id)

    return {
        "success": True,
        "message_fr": f"Contrat d'armement signe entre {seller.name_fr} et {buyer.name_fr}",
        "effects": {
            "seller_economy_change": seller.economy - old_seller_eco,
            "buyer_military_change": buyer.military - old_buyer_mil,
            "relation_change": 10,
            "value": request.value,
            "military_dependency": f"{buyer.id} depends on {seller.id}",
        },
    }


# ==================== Power Analysis Endpoints ====================

@router.get("/power/{country_id}/global")
async def get_power_global_influence(country_id: str):
    """Get a power's global influence across all zones"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    # Calculate influence in each zone
    zone_influences = {}
    total_influence = 0
    zones_dominated = 0
    zones_contested = 0

    for zone in world.influence_zones.values():
        level = zone.influence_levels.get(country_id, 0)
        breakdown = zone.influence_breakdown.get(country_id, {})

        zone_influences[zone.id] = {
            "name": zone.name,
            "name_fr": zone.name_fr,
            "total": level,
            "breakdown": breakdown,
            "is_dominant": zone.dominant_power == country_id,
            "is_contesting": country_id in zone.contested_by,
        }

        total_influence += level
        if zone.dominant_power == country_id:
            zones_dominated += 1
        if country_id in zone.contested_by:
            zones_contested += 1

    # Military bases summary
    bases = military_base_manager.get_bases_by_owner(country_id)

    return {
        "country_id": country_id,
        "country_name": country.name,
        "country_name_fr": country.name_fr,
        "tier": country.tier,
        "total_influence": total_influence,
        "average_influence": total_influence / len(world.influence_zones) if world.influence_zones else 0,
        "zones_dominated": zones_dominated,
        "zones_contested": zones_contested,
        "military_bases": len(bases),
        "total_personnel_abroad": sum(b.personnel for b in bases),
        "zone_details": zone_influences,
    }


@router.get("/rankings")
async def get_influence_rankings():
    """Get global influence rankings"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    # Calculate total influence for each country
    country_influence = {}

    for zone in world.influence_zones.values():
        for country_id, level in zone.influence_levels.items():
            if country_id not in country_influence:
                country_influence[country_id] = {
                    "total": 0,
                    "zones_dominated": 0,
                    "zones_contested": 0,
                }
            country_influence[country_id]["total"] += level
            if zone.dominant_power == country_id:
                country_influence[country_id]["zones_dominated"] += 1
            if country_id in zone.contested_by:
                country_influence[country_id]["zones_contested"] += 1

    # Sort by total influence
    rankings = []
    for country_id, data in sorted(
        country_influence.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    ):
        country = world.get_country(country_id)
        if country:
            rankings.append({
                "rank": len(rankings) + 1,
                "country_id": country_id,
                "name": country.name,
                "name_fr": country.name_fr,
                "tier": country.tier,
                "total_influence": data["total"],
                "zones_dominated": data["zones_dominated"],
                "zones_contested": data["zones_contested"],
            })

    return {
        "rankings": rankings,
        "total_zones": len(world.influence_zones),
    }


# ==================== Reference Data Endpoints ====================

@router.get("/religions")
async def list_religions():
    """List all religions in the game"""
    import json
    from pathlib import Path

    data_path = Path(__file__).parent.parent / "data" / "religions.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            religions = json.load(f)
        return {"religions": religions}
    except Exception as e:
        logger.error(f"Error loading religions: {e}")
        raise HTTPException(status_code=500, detail="Could not load religions data")


@router.get("/cultures")
async def list_cultures():
    """List all cultures in the game"""
    import json
    from pathlib import Path

    data_path = Path(__file__).parent.parent / "data" / "cultures.json"
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            cultures = json.load(f)
        return {"cultures": cultures}
    except Exception as e:
        logger.error(f"Error loading cultures: {e}")
        raise HTTPException(status_code=500, detail="Could not load cultures data")


# ==================== Helper Functions ====================

def _get_world():
    """Get the current world state from the game state module"""
    try:
        from api.game_state import get_world
        return get_world()
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not import game_state: {e}")
    return None
