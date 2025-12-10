"""Summit negotiations routes for Historia Lite"""
from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from engine.summit_negotiations import (
    negotiation_manager,
    ResolutionTopic,
    VotePosition,
)
from api.game_state import get_world

router = APIRouter(prefix="/api", tags=["negotiations"])


class ProposeResolutionRequest(BaseModel):
    """Request to propose a resolution"""
    summit_id: str
    proposer_country_id: str
    topic: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    target_country_id: Optional[str] = None
    effects: Optional[Dict] = None
    vote_type: str = "majority"


class ResolutionResponse(BaseModel):
    """Response for a resolution"""
    id: str
    title: str
    title_fr: str
    description: str
    description_fr: str
    topic: str
    proposer_country: str
    target_country: Optional[str]
    vote_type: str
    effects_if_passed: Dict


class LobbyRequest(BaseModel):
    """Request to lobby a country"""
    lobbyer_country_id: str
    target_country_id: str
    resolution_id: str
    desired_position: str


class VoteDealRequest(BaseModel):
    """Request to propose a vote deal"""
    proposer_country_id: str
    target_country_id: str
    resolution_id: str
    requested_vote: str
    compensation: Dict


class CoalitionRequest(BaseModel):
    """Request to form a coalition"""
    leader_country_id: str
    resolution_id: str
    position: str
    summit_id: str
    name: Optional[str] = None
    name_fr: Optional[str] = None


class VotePredictionResponse(BaseModel):
    """Response for vote prediction"""
    resolution_id: str
    for_count: int
    against_count: int
    abstain_count: int
    details: Dict


class SkipNegotiationsRequest(BaseModel):
    resolution_id: str
    participants: List[str]
    reason: str = "time_constraint"


class AutoNegotiateRequest(BaseModel):
    resolution_id: str
    player_country_id: str
    participants: List[str]
    rounds: int = 3


@router.post("/negotiations/resolution", response_model=ResolutionResponse)
async def propose_resolution(request: ProposeResolutionRequest):
    """Propose a new resolution for a summit"""
    world = get_world()
    proposer = world.get_country(request.proposer_country_id.upper())

    if not proposer:
        raise HTTPException(status_code=404, detail=f"Country {request.proposer_country_id} not found")

    try:
        topic = ResolutionTopic(request.topic)
    except ValueError:
        valid_topics = [t.value for t in ResolutionTopic]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid topic. Valid topics: {valid_topics}"
        )

    resolution = negotiation_manager.propose_resolution(
        summit_id=request.summit_id,
        proposer=proposer,
        topic=topic,
        title=request.title,
        title_fr=request.title_fr,
        description=request.description,
        description_fr=request.description_fr,
        target_country=request.target_country_id.upper() if request.target_country_id else None,
        effects=request.effects,
        vote_type=request.vote_type
    )

    return ResolutionResponse(
        id=resolution.id,
        title=resolution.title,
        title_fr=resolution.title_fr,
        description=resolution.description,
        description_fr=resolution.description_fr,
        topic=resolution.topic.value,
        proposer_country=resolution.proposer_country,
        target_country=resolution.target_country,
        vote_type=resolution.vote_type,
        effects_if_passed=resolution.effects_if_passed
    )


@router.get("/negotiations/resolutions", response_model=List[ResolutionResponse])
async def get_active_resolutions():
    """Get all active resolutions"""
    resolutions = list(negotiation_manager.active_resolutions.values())
    return [
        ResolutionResponse(
            id=r.id,
            title=r.title,
            title_fr=r.title_fr,
            description=r.description,
            description_fr=r.description_fr,
            topic=r.topic.value,
            proposer_country=r.proposer_country,
            target_country=r.target_country,
            vote_type=r.vote_type,
            effects_if_passed=r.effects_if_passed
        )
        for r in resolutions
    ]


@router.post("/negotiations/initialize-votes/{resolution_id}")
async def initialize_votes(resolution_id: str, participants: List[str]):
    """Initialize vote intentions for a resolution"""
    world = get_world()

    resolution = negotiation_manager.active_resolutions.get(resolution_id)
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    negotiation_manager.initialize_vote_intents(resolution, participants, world)

    return {
        "status": "success",
        "resolution_id": resolution_id,
        "participants": len(participants)
    }


@router.post("/negotiations/lobby")
async def lobby_country(request: LobbyRequest):
    """Lobby a country to change their vote"""
    world = get_world()

    lobbyer = world.get_country(request.lobbyer_country_id.upper())
    target = world.get_country(request.target_country_id.upper())

    if not lobbyer:
        raise HTTPException(status_code=404, detail="Lobbyer country not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target country not found")

    try:
        desired_position = VotePosition(request.desired_position)
    except ValueError:
        valid_positions = [p.value for p in VotePosition]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position. Valid positions: {valid_positions}"
        )

    success, message = negotiation_manager.lobby_country(
        lobbyer=lobbyer,
        target=target,
        resolution_id=request.resolution_id,
        desired_position=desired_position
    )

    return {
        "success": success,
        "message": message,
        "lobbyer": lobbyer.id,
        "target": target.id,
        "soft_power_remaining": lobbyer.soft_power
    }


@router.post("/negotiations/deal/propose")
async def propose_vote_deal(request: VoteDealRequest):
    """Propose a vote trading deal"""
    world = get_world()

    proposer = world.get_country(request.proposer_country_id.upper())
    target = world.get_country(request.target_country_id.upper())

    if not proposer:
        raise HTTPException(status_code=404, detail="Proposer country not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target country not found")

    try:
        requested_vote = VotePosition(request.requested_vote)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vote position")

    deal = negotiation_manager.propose_vote_deal(
        proposer=proposer,
        target=target,
        resolution_id=request.resolution_id,
        requested_vote=requested_vote,
        compensation=request.compensation,
        year=world.year
    )

    if not target.is_player:
        accepted, reason = negotiation_manager.evaluate_deal(deal, target, world)
        if accepted:
            negotiation_manager.accept_deal(deal.id, world)
            return {
                "deal_id": deal.id,
                "status": "accepted",
                "message": f"{target.name_fr} accepte l'accord",
                "message_fr": reason
            }
        else:
            negotiation_manager.reject_deal(deal.id)
            return {
                "deal_id": deal.id,
                "status": "rejected",
                "message": f"{target.name_fr} refuse l'accord",
                "message_fr": reason
            }

    return {
        "deal_id": deal.id,
        "status": "pending",
        "message": "Deal proposed, awaiting response"
    }


@router.post("/negotiations/deal/{deal_id}/accept")
async def accept_deal(deal_id: str):
    """Accept a pending vote deal"""
    world = get_world()
    success = negotiation_manager.accept_deal(deal_id, world)

    if not success:
        raise HTTPException(status_code=404, detail="Deal not found")

    return {"status": "accepted", "deal_id": deal_id}


@router.post("/negotiations/deal/{deal_id}/reject")
async def reject_deal(deal_id: str):
    """Reject a pending vote deal"""
    success = negotiation_manager.reject_deal(deal_id)

    if not success:
        raise HTTPException(status_code=404, detail="Deal not found")

    return {"status": "rejected", "deal_id": deal_id}


@router.get("/negotiations/deals/pending")
async def get_pending_deals():
    """Get all pending vote deals"""
    deals = list(negotiation_manager.pending_deals.values())
    return [
        {
            "id": d.id,
            "proposer": d.proposer,
            "target": d.target,
            "resolution_id": d.resolution_id,
            "requested_vote": d.requested_vote.value,
            "compensation": d.offered_compensation,
            "status": d.status
        }
        for d in deals
    ]


@router.post("/negotiations/coalition")
async def form_coalition(request: CoalitionRequest):
    """Form a coalition for a resolution"""
    world = get_world()

    leader = world.get_country(request.leader_country_id.upper())
    if not leader:
        raise HTTPException(status_code=404, detail="Leader country not found")

    try:
        position = VotePosition(request.position)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid position")

    coalition = negotiation_manager.form_coalition(
        leader=leader,
        resolution_id=request.resolution_id,
        position=position,
        summit_id=request.summit_id,
        year=world.year,
        name=request.name,
        name_fr=request.name_fr
    )

    return {
        "coalition_id": coalition.id,
        "name": coalition.name,
        "name_fr": coalition.name_fr,
        "leader": coalition.leader,
        "position": coalition.position.value,
        "members": coalition.members
    }


@router.post("/negotiations/coalition/{coalition_id}/join")
async def join_coalition(coalition_id: str, country_id: str):
    """Join an existing coalition"""
    world = get_world()

    country = world.get_country(country_id.upper())
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    success, message = negotiation_manager.join_coalition(country, coalition_id)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "status": "joined",
        "coalition_id": coalition_id,
        "country_id": country_id.upper(),
        "message": message
    }


@router.get("/negotiations/coalitions")
async def get_active_coalitions():
    """Get all active coalitions"""
    coalitions = [c for c in negotiation_manager.active_coalitions.values() if c.is_active]
    return [
        {
            "id": c.id,
            "name": c.name,
            "name_fr": c.name_fr,
            "leader": c.leader,
            "members": c.members,
            "target_resolution": c.target_resolution,
            "position": c.position.value,
            "summit_id": c.summit_id
        }
        for c in coalitions
    ]


@router.get("/negotiations/vote-prediction/{resolution_id}", response_model=VotePredictionResponse)
async def get_vote_prediction(resolution_id: str):
    """Get current vote prediction for a resolution"""
    prediction = negotiation_manager.get_vote_prediction(resolution_id)

    if "error" in prediction:
        raise HTTPException(status_code=404, detail=prediction["error"])

    return VotePredictionResponse(
        resolution_id=resolution_id,
        for_count=prediction["for"],
        against_count=prediction["against"],
        abstain_count=prediction["abstain"],
        details=prediction["details"]
    )


@router.post("/negotiations/conduct-vote/{resolution_id}")
async def conduct_vote(resolution_id: str):
    """Conduct the final vote on a resolution"""
    world = get_world()

    resolution = negotiation_manager.active_resolutions.get(resolution_id)
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    participants = list(negotiation_manager.vote_intents.get(resolution_id, {}).keys())
    if not participants:
        raise HTTPException(status_code=400, detail="No vote intents initialized")

    passed, results = negotiation_manager.conduct_vote(resolution, participants, world)

    negotiation_manager.apply_vote_consequences(resolution, results, world)

    return {
        "resolution_id": resolution_id,
        "passed": passed,
        "results": results,
        "message_fr": f"Resolution {'adoptee' if passed else 'rejetee'}: {results['for']} pour, {results['against']} contre, {results['abstain']} abstentions"
    }


@router.post("/negotiations/skip")
async def skip_negotiations(request: SkipNegotiationsRequest):
    """Skip negotiations and go directly to vote"""
    world = get_world()

    resolution = negotiation_manager.active_resolutions.get(request.resolution_id)
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    passed, results = negotiation_manager.skip_negotiations(
        resolution,
        request.participants,
        world,
        request.reason
    )

    negotiation_manager.apply_vote_consequences(resolution, results, world)

    reason_messages = {
        "time_constraint": "Negociations passees (manque de temps)",
        "different_objective": "Negociations passees (objectif different)",
        "no_interest": "Negociations passees (pas d'interet)",
    }

    return {
        "resolution_id": request.resolution_id,
        "passed": passed,
        "results": results,
        "message_fr": reason_messages.get(request.reason, "Negociations passees"),
        "vote_message_fr": f"Resolution {'adoptee' if passed else 'rejetee'}: {results['for']} pour, {results['against']} contre, {results['abstain']} abstentions"
    }


@router.post("/negotiations/auto")
async def auto_negotiate(request: AutoNegotiateRequest):
    """Auto-negotiate: AI plays the negotiation on behalf of the player"""
    world = get_world()

    resolution = negotiation_manager.active_resolutions.get(request.resolution_id)
    if not resolution:
        raise HTTPException(status_code=404, detail="Resolution not found")

    summary = negotiation_manager.auto_negotiate(
        resolution,
        request.player_country_id,
        request.participants,
        world,
        request.rounds
    )

    passed, results = negotiation_manager.conduct_vote(
        resolution,
        request.participants,
        world
    )

    negotiation_manager.apply_vote_consequences(resolution, results, world)

    return {
        "resolution_id": request.resolution_id,
        "auto_negotiation_summary": summary,
        "passed": passed,
        "results": results,
        "message_fr": f"Negociation automatique terminee: {len(summary['lobbying_done'])} lobbying, {len(summary['position_changes'])} positions changees",
        "vote_message_fr": f"Resolution {'adoptee' if passed else 'rejetee'}: {results['for']} pour, {results['against']} contre, {results['abstain']} abstentions"
    }
