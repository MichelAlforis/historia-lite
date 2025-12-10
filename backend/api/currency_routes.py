"""Currency and monetary system API routes"""
import logging
from typing import Optional, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.currency import (
    currency_manager,
    CurrencyDependency,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/currency", tags=["currency"])


# ==================== Request/Response Models ====================

class ChangeCurrencyRequest(BaseModel):
    country_id: str
    new_currency_id: str
    dependency: str  # sovereign, soft_peg, hard_peg, currency_union, dollarized, crypto_legal


class AdoptCryptoRequest(BaseModel):
    country_id: str
    level: int = 10
    as_legal_tender: bool = False


class LaunchCBDCRequest(BaseModel):
    country_id: str


class ImposeCurrencyRequest(BaseModel):
    imposer_id: str
    target_id: str
    currency_id: str
    method: str  # colonial, economic_pressure, debt_trap, regime_change, treaty


class ResistImpositionRequest(BaseModel):
    country_id: str
    imposer_id: str
    method: str  # nationalise, join_rival_bloc, default, crypto_escape, popular_uprising


class PetroAgreementRequest(BaseModel):
    oil_exporter: str
    currency_id: str
    year: int = 2025


class BreakPetroAgreementRequest(BaseModel):
    oil_exporter: str
    currency_id: str
    new_currency_id: Optional[str] = None


class ResolveCrisisRequest(BaseModel):
    crisis_id: str
    method: str  # imf_bailout, austerity, default, dollarization, devaluation


class InitializeStatusRequest(BaseModel):
    country_id: str
    currency_id: str
    dependency: str = "sovereign"


# ==================== Currency Info Endpoints ====================

@router.get("/list")
async def list_currencies():
    """List all available currencies"""
    return {
        "currencies": [
            {
                "id": c.id,
                "name": c.name,
                "name_fr": c.name_fr,
                "symbol": c.symbol,
                "type": c.type,
                "controller": c.controller,
                "is_reserve": c.is_reserve_currency,
                "global_share": c.global_share,
                "stability": c.stability,
                "description_fr": c.description_fr,
            }
            for c in currency_manager.currencies.values()
        ]
    }


@router.get("/country/{country_id}/status")
async def get_country_monetary_status(country_id: str):
    """Get monetary status of a country"""
    status = currency_manager.country_status.get(country_id)
    if not status:
        return {
            "country_id": country_id,
            "initialized": False,
            "message": "Status monetaire non initialise"
        }

    currency = currency_manager.get_currency(status.currency_id)

    return {
        "country_id": country_id,
        "initialized": True,
        "status": status.model_dump(),
        "currency_name_fr": currency.name_fr if currency else "Inconnu",
    }


# ==================== Currency Management Endpoints ====================

@router.post("/initialize")
async def initialize_country_status(request: InitializeStatusRequest):
    """Initialize monetary status for a country"""
    try:
        dependency = CurrencyDependency(request.dependency)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dependency: {request.dependency}"
        )

    status = currency_manager.initialize_country_status(
        request.country_id,
        request.currency_id,
        dependency
    )

    return {
        "success": True,
        "status": status.model_dump(),
        "message_fr": f"Status monetaire initialise pour {request.country_id}"
    }


@router.post("/change")
async def change_currency(request: ChangeCurrencyRequest):
    """Change a country's currency"""
    try:
        dependency = CurrencyDependency(request.dependency)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dependency: {request.dependency}"
        )

    success, message, effects = currency_manager.change_currency(
        request.country_id,
        request.new_currency_id,
        dependency
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


@router.post("/adopt-crypto")
async def adopt_crypto(request: AdoptCryptoRequest):
    """Adopt cryptocurrency"""
    success, message, effects = currency_manager.adopt_crypto(
        request.country_id,
        request.level,
        request.as_legal_tender
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


@router.post("/launch-cbdc")
async def launch_cbdc(request: LaunchCBDCRequest):
    """Launch a Central Bank Digital Currency"""
    success, message, effects = currency_manager.launch_cbdc(request.country_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


# ==================== Currency Domination Endpoints ====================

@router.post("/impose")
async def impose_currency(request: ImposeCurrencyRequest):
    """Force a country to adopt your currency"""
    success, message, effects = currency_manager.impose_currency(
        request.imposer_id,
        request.target_id,
        request.currency_id,
        request.method
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


@router.post("/resist")
async def resist_currency_imposition(request: ResistImpositionRequest):
    """Resist currency imposition"""
    success, message, effects = currency_manager.resist_currency_imposition(
        request.country_id,
        request.imposer_id,
        request.method
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


# ==================== Petro-Currency Endpoints ====================

@router.get("/petro/status")
async def get_petro_status():
    """Get global petro-currency status"""
    petro_dollar_strength = currency_manager.calculate_petro_dollar_strength()

    agreements = [
        {
            "id": a.id,
            "oil_exporter": a.oil_exporter,
            "currency_id": a.currency_id,
            "controller": a.controller,
            "year_signed": a.year_signed,
            "is_active": a.is_active,
        }
        for a in currency_manager.petro_agreements.values()
    ]

    return {
        "petro_dollar_strength": petro_dollar_strength,
        "total_agreements": len(agreements),
        "agreements": agreements,
        "usd_power": currency_manager.get_petro_currency_power("USD"),
        "cny_power": currency_manager.get_petro_currency_power("CNY"),
        "eur_power": currency_manager.get_petro_currency_power("EUR"),
    }


@router.post("/petro/initialize")
async def initialize_petro_dollar():
    """Initialize historical petro-dollar system"""
    currency_manager.initialize_petro_dollar_system()

    return {
        "success": True,
        "message_fr": "Systeme petro-dollar initialise",
        "petro_dollar_strength": currency_manager.calculate_petro_dollar_strength(),
    }


@router.post("/petro/sign")
async def sign_petro_agreement(request: PetroAgreementRequest):
    """Sign a petro-currency agreement"""
    success, message, effects = currency_manager.sign_petro_agreement(
        request.oil_exporter,
        request.currency_id,
        request.year
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


@router.post("/petro/break")
async def break_petro_agreement(request: BreakPetroAgreementRequest):
    """Break a petro-currency agreement (major geopolitical move!)"""
    success, message, effects = currency_manager.break_petro_agreement(
        request.oil_exporter,
        request.currency_id,
        request.new_currency_id
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
        "warning": "Ceci est un evenement geopolitique majeur!" if "world_tension" in effects else None
    }


# ==================== Crisis Endpoints ====================

@router.get("/crises")
async def list_crises():
    """List active currency crises"""
    return {
        "crises": [
            {
                "id": c.id,
                "country_id": c.country_id,
                "currency_id": c.currency_id,
                "year": c.year,
                "severity": c.severity,
                "cause": c.cause,
                "effects": c.effects,
                "resolved": c.resolved,
            }
            for c in currency_manager.active_crises
        ]
    }


@router.post("/crisis/resolve")
async def resolve_crisis(request: ResolveCrisisRequest):
    """Resolve a currency crisis"""
    success, message, effects = currency_manager.resolve_crisis(
        request.crisis_id,
        request.method
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message_fr": message,
        "effects": effects,
    }


# ==================== Analysis Endpoints ====================

@router.get("/reserve-currencies")
async def get_reserve_currencies():
    """Get all reserve currencies and their global share"""
    reserves = [
        {
            "id": c.id,
            "name_fr": c.name_fr,
            "controller": c.controller,
            "global_share": c.global_share,
            "stability": c.stability,
        }
        for c in currency_manager.currencies.values()
        if c.is_reserve_currency
    ]

    # Sort by global share
    reserves.sort(key=lambda x: x["global_share"], reverse=True)

    return {
        "reserve_currencies": reserves,
        "total_share": sum(r["global_share"] for r in reserves),
    }


@router.get("/zones")
async def get_currency_zones():
    """Get currency zones (shared currencies)"""
    zones = []

    for currency in currency_manager.currencies.values():
        if currency.members:
            zones.append({
                "currency_id": currency.id,
                "name_fr": currency.name_fr,
                "controller": currency.controller,
                "type": currency.type,
                "members": currency.members,
                "member_count": len(currency.members),
                "pegged_to": currency.pegged_to,
                "peg_rate": currency.peg_rate,
            })

    return {"currency_zones": zones}


# ==================== Single Currency Lookup (must be last!) ====================

@router.get("/{currency_id}")
async def get_currency(currency_id: str):
    """Get details of a specific currency"""
    currency = currency_manager.get_currency(currency_id)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    influence = currency_manager.get_currency_influence(currency_id)
    petro_power = currency_manager.get_petro_currency_power(currency_id)

    return {
        "currency": currency.model_dump(),
        "influence": influence,
        "petro_power": petro_power,
    }
