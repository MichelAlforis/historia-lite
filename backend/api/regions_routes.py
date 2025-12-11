"""API routes for subnational regions in Historia Lite"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from engine.region import SubnationalRegion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/regions", tags=["regions"])


class RegionCache:
    """Cache with TTL and indexes for regions data"""

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, SubnationalRegion] = {}
        self._last_load: float = 0
        self._ttl = ttl_seconds

        # Indexes for fast queries
        self._by_country: Dict[str, List[str]] = {}
        self._coastal: List[str] = []
        self._capital: List[str] = []
        self._with_resources: List[str] = []
        self._by_type: Dict[str, List[str]] = {}

    def is_expired(self) -> bool:
        """Check if cache has expired"""
        return time.time() - self._last_load > self._ttl

    def get(self, force_reload: bool = False) -> Dict[str, SubnationalRegion]:
        """Get cached regions, reload if expired"""
        if force_reload or not self._cache or self.is_expired():
            self._load()
        return self._cache

    def get_region(self, region_id: str) -> Optional[SubnationalRegion]:
        """Get a single region by ID"""
        self.get()  # Ensure cache is loaded
        return self._cache.get(region_id.upper())

    def get_by_country(self, country_id: str) -> List[SubnationalRegion]:
        """Get regions by country (uses index)"""
        self.get()  # Ensure cache is loaded
        region_ids = self._by_country.get(country_id.upper(), [])
        return [self._cache[rid] for rid in region_ids if rid in self._cache]

    def get_coastal(self) -> List[SubnationalRegion]:
        """Get coastal regions (uses index)"""
        self.get()
        return [self._cache[rid] for rid in self._coastal if rid in self._cache]

    def get_capitals(self) -> List[SubnationalRegion]:
        """Get capital regions (uses index)"""
        self.get()
        return [self._cache[rid] for rid in self._capital if rid in self._cache]

    def get_with_resources(self) -> List[SubnationalRegion]:
        """Get regions with resources (uses index)"""
        self.get()
        return [self._cache[rid] for rid in self._with_resources if rid in self._cache]

    def get_by_type(self, region_type: str) -> List[SubnationalRegion]:
        """Get regions by type (uses index)"""
        self.get()
        region_ids = self._by_type.get(region_type, [])
        return [self._cache[rid] for rid in region_ids if rid in self._cache]

    def invalidate(self):
        """Force cache invalidation"""
        self._last_load = 0

    def get_stats(self) -> dict:
        """Get cache statistics for monitoring"""
        self.get()  # Ensure cache is loaded
        age = time.time() - self._last_load if self._last_load else 0
        return {
            "total_regions": len(self._cache),
            "countries_indexed": len(self._by_country),
            "coastal_regions": len(self._coastal),
            "capital_regions": len(self._capital),
            "resource_regions": len(self._with_resources),
            "region_types": len(self._by_type),
            "cache_age_seconds": round(age, 1),
            "ttl_seconds": self._ttl,
            "expires_in_seconds": max(0, round(self._ttl - age, 1)),
            "is_expired": self.is_expired(),
        }

    def _load(self):
        """Load regions and build indexes"""
        self._cache.clear()
        self._by_country.clear()
        self._coastal.clear()
        self._capital.clear()
        self._with_resources.clear()
        self._by_type.clear()

        data_path = Path(__file__).parent.parent / "data" / "regions.json"
        if not data_path.exists():
            logger.warning(f"Regions file not found: {data_path}")
            return

        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for region_data in data.get("regions", []):
                region = SubnationalRegion(**region_data)
                self._cache[region.id] = region
                self._build_indexes(region)

            self._last_load = time.time()
            logger.info(
                f"Loaded {len(self._cache)} regions, "
                f"indexed: {len(self._by_country)} countries, "
                f"{len(self._coastal)} coastal, {len(self._capital)} capitals"
            )
        except Exception as e:
            logger.error(f"Error loading regions: {e}")

    def _build_indexes(self, region: SubnationalRegion):
        """Build indexes for a region"""
        # By country
        if region.country_id not in self._by_country:
            self._by_country[region.country_id] = []
        self._by_country[region.country_id].append(region.id)

        # By type
        if region.region_type not in self._by_type:
            self._by_type[region.region_type] = []
        self._by_type[region.region_type].append(region.id)

        # Coastal
        if region.is_coastal:
            self._coastal.append(region.id)

        # Capital
        if region.is_capital_region:
            self._capital.append(region.id)

        # Resources
        if region.has_oil or region.has_strategic_resources:
            self._with_resources.append(region.id)


# Global cache instance
_region_cache = RegionCache(ttl_seconds=300)  # 5 minute TTL


def _load_regions() -> Dict[str, SubnationalRegion]:
    """Load regions from cache (backwards compatible)"""
    return _region_cache.get()


def _get_region_or_404(region_id: str) -> SubnationalRegion:
    """Get region or raise 404"""
    region = _region_cache.get_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")
    return region


# Response schemas
class SubnationalRegionResponse(BaseModel):
    id: str
    country_id: str
    name: str
    name_fr: str
    region_type: str
    power_score: int
    strategic_value: int
    population_share: int
    economic_share: int
    military_presence: int
    is_capital_region: bool
    is_border_region: bool
    is_coastal: bool
    has_oil: bool
    has_strategic_resources: bool
    resource_type: Optional[str]
    attack_difficulty: int
    strategic_importance: int

    @classmethod
    def from_region(cls, region: SubnationalRegion) -> "SubnationalRegionResponse":
        return cls(
            id=region.id,
            country_id=region.country_id,
            name=region.name,
            name_fr=region.name_fr,
            region_type=region.region_type,
            power_score=region.power_score,
            strategic_value=region.strategic_value,
            population_share=region.population_share,
            economic_share=region.economic_share,
            military_presence=region.military_presence,
            is_capital_region=region.is_capital_region,
            is_border_region=region.is_border_region,
            is_coastal=region.is_coastal,
            has_oil=region.has_oil,
            has_strategic_resources=region.has_strategic_resources,
            resource_type=region.resource_type,
            attack_difficulty=region.get_attack_difficulty(),
            strategic_importance=region.get_strategic_importance(),
        )


class RegionsSummaryResponse(BaseModel):
    total: int
    by_country: Dict[str, int]
    by_region_type: Dict[str, int]
    capital_regions: int
    coastal_regions: int
    resource_regions: int


class AttackInfoResponse(BaseModel):
    region_id: str
    region_name: str
    country_id: str
    attack_difficulty: int
    strategic_importance: int
    population_share: int
    economic_share: int
    is_capital_region: bool
    is_coastal: bool
    has_resources: bool
    attack_types: List[Dict[str, str]]
    potential_consequences: List[str]


class RegionAttackRequest(BaseModel):
    """Request schema for attacking a region"""
    attacker_id: str
    attack_type: str  # "limited_strike", "invasion", "blockade"


class RegionAttackResult(BaseModel):
    """Result of an attack on a region"""
    success: bool
    damage_dealt: int
    casualties_attacker: int
    casualties_defender: int
    region_damage: int  # Damage to region infrastructure
    message: str
    message_fr: str
    consequences: List[str]
    region_status: SubnationalRegionResponse


@router.get("", response_model=List[SubnationalRegionResponse])
async def get_regions(
    country_id: Optional[str] = Query(None, description="Filter by parent country ISO3 code"),
    region_type: Optional[str] = Query(None, description="Filter by region type"),
    has_resources: Optional[bool] = Query(None, description="Filter regions with resources"),
    is_coastal: Optional[bool] = Query(None, description="Filter coastal regions"),
):
    """Get all subnational regions with optional filters (optimized with indexes)"""
    # Use indexed queries when possible
    if country_id and not region_type and has_resources is None and is_coastal is None:
        # Fast path: country-only filter uses index
        regions_list = _region_cache.get_by_country(country_id)
    elif is_coastal is True and not country_id and not region_type and has_resources is None:
        # Fast path: coastal-only filter uses index
        regions_list = _region_cache.get_coastal()
    elif has_resources is True and not country_id and not region_type and is_coastal is None:
        # Fast path: resources-only filter uses index
        regions_list = _region_cache.get_with_resources()
    elif region_type and not country_id and has_resources is None and is_coastal is None:
        # Fast path: type-only filter uses index
        regions_list = _region_cache.get_by_type(region_type)
    else:
        # Slow path: full scan with multiple filters
        regions = _region_cache.get()
        regions_list = []
        for region in regions.values():
            if country_id and region.country_id != country_id.upper():
                continue
            if region_type and region.region_type != region_type:
                continue
            if has_resources is not None:
                has_res = region.has_oil or region.has_strategic_resources
                if has_resources != has_res:
                    continue
            if is_coastal is not None and region.is_coastal != is_coastal:
                continue
            regions_list.append(region)

    result = [SubnationalRegionResponse.from_region(r) for r in regions_list]
    result.sort(key=lambda r: r.strategic_importance, reverse=True)
    return result


@router.get("/summary", response_model=RegionsSummaryResponse)
async def get_regions_summary():
    """Get summary statistics for all regions (uses pre-built indexes)"""
    # Ensure cache is loaded
    _region_cache.get()

    # Use indexes for counts - O(1) instead of O(n)
    by_country = {k: len(v) for k, v in _region_cache._by_country.items()}
    by_type = {k: len(v) for k, v in _region_cache._by_type.items()}

    return RegionsSummaryResponse(
        total=len(_region_cache._cache),
        by_country=by_country,
        by_region_type=by_type,
        capital_regions=len(_region_cache._capital),
        coastal_regions=len(_region_cache._coastal),
        resource_regions=len(_region_cache._with_resources),
    )


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring (admin endpoint)"""
    return _region_cache.get_stats()


@router.post("/cache/reload")
async def reload_cache():
    """Force cache reload (admin endpoint)"""
    _region_cache.invalidate()
    regions = _region_cache.get(force_reload=True)
    return {
        "status": "reloaded",
        "regions_count": len(regions),
        "stats": _region_cache.get_stats(),
    }


@router.get("/country/{country_id}", response_model=List[SubnationalRegionResponse])
async def get_regions_by_country(country_id: str):
    """Get all regions for a specific country (uses index)"""
    # Use indexed query instead of full scan
    regions = _region_cache.get_by_country(country_id)

    if not regions:
        raise HTTPException(
            status_code=404,
            detail=f"No regions found for country {country_id}"
        )

    result = [SubnationalRegionResponse.from_region(r) for r in regions]
    result.sort(key=lambda r: r.strategic_importance, reverse=True)
    return result


@router.get("/{region_id}", response_model=SubnationalRegionResponse)
async def get_region(region_id: str):
    """Get a specific region by ID"""
    region = _get_region_or_404(region_id)
    return SubnationalRegionResponse.from_region(region)


@router.get("/{region_id}/attack-info", response_model=AttackInfoResponse)
async def get_attack_info(region_id: str):
    """Get attack targeting information for a region"""
    region = _get_region_or_404(region_id)

    # Determine available attack types based on region characteristics
    attack_types = []

    # Limited strike is always available
    attack_types.append({
        "type": "limited_strike",
        "name": "Frappe limitee",
        "name_fr": "Frappe limitee",
        "risk": "modere",
        "description": "Frappes ciblees sur infrastructure militaire"
    })

    # Invasion requires border or coastal access
    if region.is_border_region or region.is_coastal:
        attack_types.append({
            "type": "invasion",
            "name": "Invasion",
            "name_fr": "Invasion",
            "risk": "eleve",
            "description": "Tentative de conquete de la region"
        })

    # Naval blockade only for coastal regions
    if region.is_coastal:
        attack_types.append({
            "type": "blockade",
            "name": "Blocus naval",
            "name_fr": "Blocus naval",
            "risk": "faible",
            "description": "Blocus des ports et voies maritimes"
        })

    # Determine consequences
    consequences = []
    consequences.append(f"Relations avec {region.country_id}: -50 minimum")

    if region.is_capital_region:
        consequences.append("GUERRE TOTALE probable (capitale attaquee)")
        consequences.append("Mobilisation generale de l'ennemi")

    if region.military_presence > 70:
        consequences.append("Forte resistance militaire attendue")

    if region.has_oil or region.has_strategic_resources:
        consequences.append("Perturbation des marches mondiaux")

    # Add protector consequences based on country tier (would need world state)
    consequences.append("Reactions des allies et protecteurs possibles")

    return AttackInfoResponse(
        region_id=region.id,
        region_name=region.name_fr,
        country_id=region.country_id,
        attack_difficulty=region.get_attack_difficulty(),
        strategic_importance=region.get_strategic_importance(),
        population_share=region.population_share,
        economic_share=region.economic_share,
        is_capital_region=region.is_capital_region,
        is_coastal=region.is_coastal,
        has_resources=region.has_oil or region.has_strategic_resources,
        attack_types=attack_types,
        potential_consequences=consequences,
    )


def reload_regions():
    """Force reload of regions data (useful after updates)"""
    _region_cache.invalidate()
    return _region_cache.get(force_reload=True)


def _calculate_attack_result(
    region: SubnationalRegion,
    attack_type: str,
    attacker_id: str
) -> Dict:
    """Calculate the result of an attack based on region characteristics"""
    import random

    difficulty = region.get_attack_difficulty()
    strategic_imp = region.get_strategic_importance()

    # Base success chance depends on attack type
    base_chance = {
        "limited_strike": 70,  # Easier - targeted strikes
        "invasion": 30,        # Hardest - full ground assault
        "blockade": 50,        # Medium - naval operations
    }.get(attack_type, 50)

    # Modify by difficulty
    success_chance = max(10, base_chance - (difficulty // 2))

    # Random roll
    roll = random.randint(1, 100)
    success = roll <= success_chance

    # Calculate damages
    if success:
        damage_dealt = random.randint(30, 70) + (100 - difficulty) // 3
        casualties_attacker = random.randint(5, 20) * (difficulty // 20)
        casualties_defender = random.randint(20, 50) + damage_dealt // 2
        region_damage = random.randint(10, 40) if attack_type != "blockade" else 5
    else:
        damage_dealt = random.randint(5, 25)
        casualties_attacker = random.randint(20, 50) + difficulty // 2
        casualties_defender = random.randint(10, 30)
        region_damage = random.randint(5, 15)

    # Generate consequences
    consequences = []
    consequences.append(f"Relations {attacker_id} <-> {region.country_id}: -50")

    if region.is_capital_region:
        consequences.append("ALERTE: Attaque sur capitale - guerre totale probable")
        region_damage += 10

    if strategic_imp > 70:
        consequences.append("Intervention internationale probable")

    if region.has_oil or region.has_strategic_resources:
        consequences.append("Marches mondiaux perturbes")

    if attack_type == "invasion" and success:
        consequences.append("Zone sous controle partiel de l'attaquant")
    elif attack_type == "blockade":
        consequences.append("Commerce maritime bloque")

    # Message based on success
    if success:
        message = f"Attack on {region.name} succeeded"
        message_fr = f"Attaque sur {region.name_fr} reussie"
    else:
        message = f"Attack on {region.name} repelled"
        message_fr = f"Attaque sur {region.name_fr} repoussee"

    return {
        "success": success,
        "damage_dealt": min(100, damage_dealt),
        "casualties_attacker": casualties_attacker,
        "casualties_defender": casualties_defender,
        "region_damage": min(100, region_damage),
        "message": message,
        "message_fr": message_fr,
        "consequences": consequences,
    }


@router.post("/{region_id}/attack", response_model=RegionAttackResult)
async def execute_region_attack(
    region_id: str,
    request: RegionAttackRequest,
):
    """
    Execute an attack on a specific region.

    Attack types:
    - limited_strike: Targeted military strikes (always available)
    - invasion: Ground assault (requires border or coastal access)
    - blockade: Naval blockade (coastal regions only)
    """
    region = _get_region_or_404(region_id)

    # Validate attack type
    valid_types = ["limited_strike"]
    if region.is_border_region or region.is_coastal:
        valid_types.append("invasion")
    if region.is_coastal:
        valid_types.append("blockade")

    if request.attack_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Attack type '{request.attack_type}' not valid for region {region_id}. "
                   f"Valid types: {valid_types}"
        )

    # Calculate attack result
    result = _calculate_attack_result(region, request.attack_type, request.attacker_id)

    # Return result with updated region status
    return RegionAttackResult(
        success=result["success"],
        damage_dealt=result["damage_dealt"],
        casualties_attacker=result["casualties_attacker"],
        casualties_defender=result["casualties_defender"],
        region_damage=result["region_damage"],
        message=result["message"],
        message_fr=result["message_fr"],
        consequences=result["consequences"],
        region_status=SubnationalRegionResponse.from_region(region),
    )
