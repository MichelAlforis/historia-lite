"""Economic blocs routes for Historia Lite"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from engine.bloc import bloc_manager, EconomicBloc
from schemas.game import CountryResponse
from api.game_state import get_world

router = APIRouter(prefix="/api", tags=["blocs"])


class BlocResponse(BaseModel):
    """Response schema for an economic bloc"""
    id: str
    name: str
    name_fr: str
    type: str
    members: List[str]
    economy_bonus: int
    trade_bonus: int
    tariff_external: int
    relation_bonus: int
    vote_coordination: bool
    defense_clause: bool
    leader_country: Optional[str]
    rotating_presidency: bool
    pending_applications: List[str]
    description_fr: str

    @classmethod
    def from_bloc(cls, bloc: EconomicBloc) -> "BlocResponse":
        return cls(
            id=bloc.id,
            name=bloc.name,
            name_fr=bloc.name_fr,
            type=bloc.type,
            members=bloc.members,
            economy_bonus=bloc.economy_bonus,
            trade_bonus=bloc.trade_bonus,
            tariff_external=bloc.tariff_external,
            relation_bonus=bloc.relation_bonus,
            vote_coordination=bloc.vote_coordination,
            defense_clause=bloc.defense_clause,
            leader_country=bloc.leader_country,
            rotating_presidency=bloc.rotating_presidency,
            pending_applications=bloc.pending_applications,
            description_fr=bloc.description_fr
        )


class BlocBonusResponse(BaseModel):
    """Response for country bloc bonuses"""
    country_id: str
    blocs: List[str]
    total_economy_bonus: int
    total_trade_bonus: int
    total_relation_bonus: int
    has_defense_pact: bool
    defense_allies: List[str]


@router.get("/blocs", response_model=List[BlocResponse])
async def get_all_blocs():
    """Get all economic blocs"""
    blocs = list(bloc_manager.blocs.values())
    return [BlocResponse.from_bloc(b) for b in blocs]


@router.get("/blocs/{bloc_id}", response_model=BlocResponse)
async def get_bloc(bloc_id: str):
    """Get details of a specific bloc"""
    bloc = bloc_manager.blocs.get(bloc_id.upper())
    if not bloc:
        raise HTTPException(status_code=404, detail=f"Bloc {bloc_id} not found")
    return BlocResponse.from_bloc(bloc)


@router.get("/blocs/{bloc_id}/members", response_model=List[CountryResponse])
async def get_bloc_members_detailed(bloc_id: str):
    """Get all countries in a specific bloc with full details"""
    world = get_world()
    bloc = bloc_manager.blocs.get(bloc_id.upper())
    if not bloc:
        raise HTTPException(status_code=404, detail=f"Bloc {bloc_id} not found")

    members = []
    for member_id in bloc.members:
        country = world.get_country(member_id)
        if country:
            members.append(CountryResponse.from_country(country))

    return members


@router.get("/blocs/country/{country_id}/bonuses", response_model=BlocBonusResponse)
async def get_country_bloc_bonuses(country_id: str):
    """Get all bloc bonuses for a country"""
    world = get_world()
    country = world.get_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    country_blocs = bloc_manager.get_country_blocs(country_id.upper())
    economy_bonus = bloc_manager.calculate_economy_bonus(country_id.upper())
    has_defense = bloc_manager.has_defense_clause(country_id.upper())
    defense_allies = bloc_manager.get_defense_allies(country_id.upper())

    trade_bonus = sum(bloc_manager.blocs[b].trade_bonus for b in country_blocs)
    relation_bonus = sum(bloc_manager.blocs[b].relation_bonus for b in country_blocs)

    return BlocBonusResponse(
        country_id=country_id.upper(),
        blocs=country_blocs,
        total_economy_bonus=economy_bonus,
        total_trade_bonus=trade_bonus,
        total_relation_bonus=relation_bonus,
        has_defense_pact=has_defense,
        defense_allies=defense_allies
    )


@router.post("/blocs/{bloc_id}/apply/{country_id}")
async def apply_to_bloc(bloc_id: str, country_id: str):
    """Apply for membership in a bloc"""
    world = get_world()
    country = world.get_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    bloc = bloc_manager.blocs.get(bloc_id.upper())
    if not bloc:
        raise HTTPException(status_code=404, detail=f"Bloc {bloc_id} not found")

    eligible, reason = bloc_manager.check_membership_eligible(bloc_id.upper(), country)
    if not eligible:
        return {
            "status": "rejected",
            "reason": reason,
            "bloc_id": bloc_id.upper(),
            "country_id": country_id.upper()
        }

    success, msg = bloc_manager.apply_for_membership(bloc_id.upper(), country)
    if success:
        return {
            "status": "pending",
            "message": f"{country.name} has applied to join {bloc.name}",
            "message_fr": f"{country.name_fr} a postule pour rejoindre {bloc.name_fr}",
            "bloc_id": bloc_id.upper(),
            "country_id": country_id.upper()
        }
    else:
        return {
            "status": "already_member_or_pending",
            "bloc_id": bloc_id.upper(),
            "country_id": country_id.upper()
        }
