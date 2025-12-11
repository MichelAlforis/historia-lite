"""Economy API routes - Trade, Debt, and Reserves"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.economy import (
    economy_manager,
    TradeType,
    DebtHolder,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/economy", tags=["economy"])


# ==================== Request Models ====================

class TradeAgreementRequest(BaseModel):
    country_a: str
    country_b: str
    trade_type: str = "standard"
    volume: int = Field(default=50, ge=0, le=100)


class DebtChangeRequest(BaseModel):
    country_id: str
    amount: int = Field(ge=1, le=50)
    holder: str = "foreign"


class ReservesChangeRequest(BaseModel):
    country_id: str
    amount: int = Field(ge=1, le=20)


# ==================== Trade Endpoints ====================

@router.get("/trade/{country_id}")
async def get_country_trade(country_id: str):
    """Get trade information for a country"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    partners = economy_manager.get_trade_partners(country_id)
    trade_volume = economy_manager.get_trade_volume(country_id)
    trade_balance = economy_manager.get_trade_balance(country_id)

    return {
        "country_id": country_id,
        "country_name": country.name_fr,
        "trade_partners": [
            {
                "partner_id": partner,
                "trade_type": agreement.trade_type.value,
                "volume": agreement.volume,
                "balance": agreement.balance if country_id == agreement.country_a else -agreement.balance,
                "year_signed": agreement.year_signed,
            }
            for partner, agreement in partners
        ],
        "total_volume": trade_volume,
        "trade_balance": trade_balance,
        "balance_status": "surplus" if trade_balance > 0 else "deficit" if trade_balance < 0 else "balanced",
    }


@router.post("/trade/agreement")
async def create_trade_agreement(request: TradeAgreementRequest):
    """Create a new trade agreement between two countries"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country_a = world.get_country(request.country_a)
    country_b = world.get_country(request.country_b)

    if not country_a:
        raise HTTPException(status_code=404, detail=f"Country {request.country_a} not found")
    if not country_b:
        raise HTTPException(status_code=404, detail=f"Country {request.country_b} not found")

    # Map trade type
    trade_type_map = {
        "standard": TradeType.STANDARD,
        "free_trade": TradeType.FREE_TRADE,
        "customs_union": TradeType.CUSTOMS_UNION,
        "embargo": TradeType.EMBARGO,
        "sanctions": TradeType.SANCTIONS,
    }
    trade_type = trade_type_map.get(request.trade_type, TradeType.STANDARD)

    agreement = economy_manager.create_trade_agreement(
        country_a=request.country_a,
        country_b=request.country_b,
        trade_type=trade_type,
        volume=request.volume,
        year=world.year,
    )

    # Improve relations
    country_a.modify_relation(request.country_b, 5)
    country_b.modify_relation(request.country_a, 5)

    return {
        "success": True,
        "agreement": {
            "id": agreement.id,
            "country_a": agreement.country_a,
            "country_b": agreement.country_b,
            "trade_type": agreement.trade_type.value,
            "volume": agreement.volume,
        },
        "message_fr": f"Accord commercial signe entre {country_a.name_fr} et {country_b.name_fr}",
    }


@router.get("/trade/global")
async def get_global_trade():
    """Get global trade statistics"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    agreements = list(economy_manager.trade_agreements.values())
    active_agreements = [a for a in agreements if a.is_active]

    # Calculate top traders
    trade_volumes = {}
    for country in world.get_all_countries():
        trade_volumes[country.id] = economy_manager.get_trade_volume(country.id)

    top_traders = sorted(
        trade_volumes.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return {
        "total_agreements": len(agreements),
        "active_agreements": len(active_agreements),
        "top_traders": [
            {"country_id": cid, "volume": vol}
            for cid, vol in top_traders
        ],
        "trade_types": {
            tt.value: len([a for a in active_agreements if a.trade_type == tt])
            for tt in TradeType
        },
    }


# ==================== Debt Endpoints ====================

@router.get("/debt/{country_id}")
async def get_country_debt(country_id: str):
    """Get debt information for a country"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    debt = economy_manager.get_or_create_debt(country_id)

    return {
        "country_id": country_id,
        "country_name": country.name_fr,
        "debt_to_gdp": debt.debt_to_gdp,
        "credit_rating": debt.credit_rating,
        "interest_rate": debt.interest_rate,
        "foreign_debt_share": debt.foreign_debt_share,
        "debt_holders": debt.debt_holders,
        "is_in_default": debt.is_in_default,
        "default_year": debt.default_year,
        "risk_level": _get_debt_risk_level(debt.debt_to_gdp),
    }


@router.post("/debt/increase")
async def increase_debt(request: DebtChangeRequest):
    """Increase country's debt (e.g., borrowing)"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(request.country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {request.country_id} not found")

    # Map holder
    holder_map = {
        "domestic": DebtHolder.DOMESTIC,
        "foreign": DebtHolder.FOREIGN,
        "imf": DebtHolder.IMF,
        "world_bank": DebtHolder.WORLD_BANK,
        "china": DebtHolder.CHINA,
    }
    holder = holder_map.get(request.holder, DebtHolder.FOREIGN)

    debt = economy_manager.increase_debt(
        country_id=request.country_id,
        amount=request.amount,
        holder=holder,
    )

    # Debt gives short-term economic boost
    country.economy = min(100, country.economy + request.amount // 5)

    return {
        "success": True,
        "new_debt_to_gdp": debt.debt_to_gdp,
        "credit_rating": debt.credit_rating,
        "message_fr": f"{country.name_fr} a emprunte {request.amount}% du PIB",
    }


@router.post("/debt/pay")
async def pay_debt(request: DebtChangeRequest):
    """Pay down country's debt"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(request.country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {request.country_id} not found")

    debt = economy_manager.pay_debt(
        country_id=request.country_id,
        amount=request.amount,
    )

    return {
        "success": True,
        "new_debt_to_gdp": debt.debt_to_gdp,
        "credit_rating": debt.credit_rating,
        "message_fr": f"{country.name_fr} a rembourse {request.amount}% de sa dette",
    }


# ==================== Reserves Endpoints ====================

@router.get("/reserves/{country_id}")
async def get_country_reserves(country_id: str):
    """Get foreign reserves for a country"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    reserves = economy_manager.get_or_create_reserves(country_id)

    return {
        "country_id": country_id,
        "country_name": country.name_fr,
        "total_reserves_months": reserves.total_reserves,
        "composition": {
            "usd": reserves.usd_share,
            "eur": reserves.eur_share,
            "gold": reserves.gold_share,
            "cny": reserves.cny_share,
            "other": reserves.other_share,
        },
        "health": _get_reserves_health(reserves.total_reserves),
    }


# ==================== Economic Summary ====================

@router.get("/summary/{country_id}")
async def get_economic_summary(country_id: str):
    """Get comprehensive economic summary for a country"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    country = world.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    summary = economy_manager.get_economic_summary(country_id)
    summary["country_name"] = country.name_fr
    summary["economy_score"] = country.economy

    return summary


@router.get("/global/rankings")
async def get_economic_rankings():
    """Get global economic rankings"""
    world = _get_world()
    if not world:
        raise HTTPException(status_code=500, detail="World not initialized")

    rankings = []
    for country in world.get_all_countries():
        summary = economy_manager.get_economic_summary(country.id)
        rankings.append({
            "country_id": country.id,
            "name": country.name_fr,
            "tier": country.tier,
            "economy": country.economy,
            "trade_volume": summary["trade"]["total_volume"],
            "debt_to_gdp": summary["debt"]["debt_to_gdp"],
            "credit_rating": summary["debt"]["credit_rating"],
            "health": summary["health"],
        })

    # Sort by economy score
    rankings.sort(key=lambda x: x["economy"], reverse=True)

    return {
        "rankings": rankings[:20],
        "total_countries": len(rankings),
    }


# ==================== Helper Functions ====================

def _get_world():
    """Get the current world state"""
    try:
        from api.game_state import get_world
        return get_world()
    except ImportError as e:
        logger.warning(f"Could not import game_state: {e}")
    return None


def _get_debt_risk_level(debt_to_gdp: int) -> str:
    """Get risk level based on debt to GDP ratio"""
    if debt_to_gdp < 40:
        return "low"
    elif debt_to_gdp < 70:
        return "moderate"
    elif debt_to_gdp < 100:
        return "elevated"
    elif debt_to_gdp < 150:
        return "high"
    else:
        return "critical"


def _get_reserves_health(months: int) -> str:
    """Get reserves health status"""
    if months >= 60:
        return "excellent"
    elif months >= 40:
        return "good"
    elif months >= 20:
        return "adequate"
    elif months >= 10:
        return "low"
    else:
        return "critical"
